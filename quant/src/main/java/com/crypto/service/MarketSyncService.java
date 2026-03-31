package com.crypto.service;

import com.crypto.config.ExchangeProperties;
import com.crypto.config.TradingProperties;
import com.crypto.enums.ExchangeEnum;
import com.crypto.enums.KlineInterval;
import com.crypto.enums.MarketType;
import com.crypto.exchange.ExchangeApiClient;
import com.crypto.exchange.ExchangeClientFactory;
import com.crypto.model.dto.DepthDTO;
import com.crypto.model.dto.KlineDTO;
import com.crypto.model.dto.TickDTO;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Async;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

import javax.annotation.PostConstruct;
import java.util.List;
import java.util.Map;

/**
 * 行情同步服务 - 定时从交易所拉取行情数据并持久化
 * 支持同时同步多个交易所的现货和合约行情
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class MarketSyncService {

    private final ExchangeClientFactory exchangeClientFactory;
    private final MarketDataService marketDataService;
    private final TradingProperties tradingProperties;
    private final ExchangeProperties exchangeProperties;

    /**
     * 启动时同步历史K线数据
     */
    @PostConstruct
    public void initHistorySync() {
        log.info("========== 启动历史行情同步 ==========");
        // 异步执行历史同步，不阻塞启动
        new Thread(() -> {
            try {
                Thread.sleep(5000); // 等待Spring完全初始化
                syncHistoryKlines();
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        }, "history-sync-init").start();
    }

    /**
     * 定时同步K线数据 (默认每分钟)
     */
    @Scheduled(fixedDelayString = "${trading.sync.kline-interval:60000}", initialDelay = 10000)
    public void scheduleSyncKlines() {
        log.info("========== 定时同步K线行情 ==========");
        syncRealtimeKlines();
    }

    /**
     * 定时同步Tick行情 (默认每5秒)
     */
    @Scheduled(fixedDelayString = "${trading.sync.tick-interval:5000}", initialDelay = 8000)
    public void scheduleSyncTicks() {
        syncTicks();
    }

    /**
     * 定时同步深度数据 (默认每10秒)
     */
    @Scheduled(fixedDelayString = "${trading.sync.depth-interval:10000}", initialDelay = 12000)
    public void scheduleSyncDepth() {
        syncDepth();
    }

    // ===================== 核心同步逻辑 =====================

    /**
     * 同步历史K线 - 首次启动时补全历史数据
     */
    private void syncHistoryKlines() {
        Map<ExchangeEnum, ExchangeApiClient> clients = exchangeClientFactory.getAllClients();
        int historyDays = tradingProperties.getSync().getHistoryDays();

        for (Map.Entry<ExchangeEnum, ExchangeApiClient> entry : clients.entrySet()) {
            ExchangeApiClient client = entry.getValue();
            String exchangeCode = entry.getKey().getCode();

            // 同步现货K线
            for (String symbol : tradingProperties.getSymbols().getSpot()) {
                for (String intervalCode : tradingProperties.getKlineIntervals()) {
                    try {
                        syncHistoryKlineForSymbol(client, exchangeCode, symbol, MarketType.SPOT,
                                KlineInterval.fromCode(intervalCode), historyDays);
                    } catch (Exception e) {
                        log.error("同步历史K线异常: exchange={}, symbol={}, interval={}",
                                exchangeCode, symbol, intervalCode, e);
                    }
                }
            }

            // 同步合约K线
            for (String symbol : tradingProperties.getSymbols().getFutures()) {
                for (String intervalCode : tradingProperties.getKlineIntervals()) {
                    try {
                        syncHistoryKlineForSymbol(client, exchangeCode, symbol, MarketType.FUTURES,
                                KlineInterval.fromCode(intervalCode), historyDays);
                    } catch (Exception e) {
                        log.error("同步历史K线异常: exchange={}, symbol={}, interval={}",
                                exchangeCode, symbol, intervalCode, e);
                    }
                }
            }
        }

        log.info("========== 历史K线同步完成 ==========");
    }

    /**
     * 同步单个交易对的历史K线
     */
    private void syncHistoryKlineForSymbol(ExchangeApiClient client, String exchange,
                                           String symbol, MarketType marketType,
                                           KlineInterval interval, int historyDays) {
        // 查找本地最新的K线时间，做增量同步
        Long latestOpenTime = marketDataService.getLatestKlineOpenTime(
                exchange, symbol, marketType.getCode(), interval.getCode());

        long startTime;
        if (latestOpenTime != null) {
            startTime = latestOpenTime + interval.getMilliseconds();
            log.info("增量同步K线: exchange={}, symbol={}, interval={}, marketType={}, from={}",
                    exchange, symbol, interval.getCode(), marketType, startTime);
        } else {
            startTime = System.currentTimeMillis() - (long) historyDays * 24 * 60 * 60 * 1000L;
            log.info("全量同步历史K线: exchange={}, symbol={}, interval={}, marketType={}, days={}",
                    exchange, symbol, interval.getCode(), marketType, historyDays);
        }

        long endTime = System.currentTimeMillis();
        int totalSaved = 0;

        // 分批获取，每批最多500/300条 (Binance 1500, OKX 300)
        while (startTime < endTime) {
            try {
                List<KlineDTO> klines = client.getKlines(symbol, marketType, interval,
                        startTime, endTime, 500);

                if (klines.isEmpty()) {
                    break;
                }

                int saved = marketDataService.saveKlines(klines);
                totalSaved += saved;

                // 更新startTime为最后一根K线之后
                KlineDTO last = klines.get(klines.size() - 1);
                startTime = last.getOpenTime() + interval.getMilliseconds();

                // 防止API频率限制
                Thread.sleep(200);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                break;
            } catch (Exception e) {
                log.error("批量获取K线异常: exchange={}, symbol={}", exchange, symbol, e);
                break;
            }
        }

        if (totalSaved > 0) {
            log.info("K线同步完成: exchange={}, symbol={}, interval={}, marketType={}, saved={}",
                    exchange, symbol, interval.getCode(), marketType, totalSaved);
        }
    }

    /**
     * 同步实时K线
     */
    @Async("marketSyncExecutor")
    public void syncRealtimeKlines() {
        Map<ExchangeEnum, ExchangeApiClient> clients = exchangeClientFactory.getAllClients();

        for (Map.Entry<ExchangeEnum, ExchangeApiClient> entry : clients.entrySet()) {
            ExchangeApiClient client = entry.getValue();
            String exchangeCode = entry.getKey().getCode();

            // 现货
            for (String symbol : tradingProperties.getSymbols().getSpot()) {
                for (String intervalCode : tradingProperties.getKlineIntervals()) {
                    try {
                        KlineInterval interval = KlineInterval.fromCode(intervalCode);
                        List<KlineDTO> klines = client.getKlines(symbol, MarketType.SPOT,
                                interval, null, null, 5);
                        if (!klines.isEmpty()) {
                            marketDataService.saveKlines(klines);
                        }
                    } catch (Exception e) {
                        log.error("同步实时K线异常: {}/{}/{}", exchangeCode, symbol, intervalCode, e);
                    }
                }
            }

            // 合约
            for (String symbol : tradingProperties.getSymbols().getFutures()) {
                for (String intervalCode : tradingProperties.getKlineIntervals()) {
                    try {
                        KlineInterval interval = KlineInterval.fromCode(intervalCode);
                        List<KlineDTO> klines = client.getKlines(symbol, MarketType.FUTURES,
                                interval, null, null, 5);
                        if (!klines.isEmpty()) {
                            marketDataService.saveKlines(klines);
                        }
                    } catch (Exception e) {
                        log.error("同步实时K线异常: {}/{}/{}", exchangeCode, symbol, intervalCode, e);
                    }
                }
            }
        }
    }

    /**
     * 同步Tick行情
     */
    @Async("marketSyncExecutor")
    public void syncTicks() {
        Map<ExchangeEnum, ExchangeApiClient> clients = exchangeClientFactory.getAllClients();

        for (Map.Entry<ExchangeEnum, ExchangeApiClient> entry : clients.entrySet()) {
            ExchangeApiClient client = entry.getValue();

            try {
                // 批量获取现货Tick
                List<String> spotSymbols = tradingProperties.getSymbols().getSpot();
                if (!spotSymbols.isEmpty()) {
                    List<TickDTO> spotTicks = client.getTickers(spotSymbols, MarketType.SPOT);
                    for (TickDTO tick : spotTicks) {
                        marketDataService.saveTick(tick);
                    }
                }

                // 批量获取合约Tick
                List<String> futuresSymbols = tradingProperties.getSymbols().getFutures();
                if (!futuresSymbols.isEmpty()) {
                    List<TickDTO> futuresTicks = client.getTickers(futuresSymbols, MarketType.FUTURES);
                    for (TickDTO tick : futuresTicks) {
                        marketDataService.saveTick(tick);
                    }
                }
            } catch (Exception e) {
                log.error("同步Tick异常: exchange={}", entry.getKey(), e);
            }
        }
    }

    /**
     * 同步深度数据
     */
    @Async("marketSyncExecutor")
    public void syncDepth() {
        Map<ExchangeEnum, ExchangeApiClient> clients = exchangeClientFactory.getAllClients();

        for (Map.Entry<ExchangeEnum, ExchangeApiClient> entry : clients.entrySet()) {
            ExchangeApiClient client = entry.getValue();

            // 现货深度
            for (String symbol : tradingProperties.getSymbols().getSpot()) {
                try {
                    DepthDTO depth = client.getDepth(symbol, MarketType.SPOT, 20);
                    marketDataService.saveDepth(depth);
                } catch (Exception e) {
                    log.error("同步现货深度异常: {}/{}", entry.getKey(), symbol, e);
                }
            }

            // 合约深度
            for (String symbol : tradingProperties.getSymbols().getFutures()) {
                try {
                    DepthDTO depth = client.getDepth(symbol, MarketType.FUTURES, 20);
                    marketDataService.saveDepth(depth);
                } catch (Exception e) {
                    log.error("同步合约深度异常: {}/{}", entry.getKey(), symbol, e);
                }
            }
        }
    }
}
