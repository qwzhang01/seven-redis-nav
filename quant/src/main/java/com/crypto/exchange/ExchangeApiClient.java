package com.crypto.exchange;

import com.crypto.enums.ExchangeEnum;
import com.crypto.enums.KlineInterval;
import com.crypto.enums.MarketType;
import com.crypto.model.dto.DepthDTO;
import com.crypto.model.dto.KlineDTO;
import com.crypto.model.dto.TickDTO;

import java.util.List;

/**
 * 交易所API统一接口 - 所有交易所对接都实现此接口
 * 调用方只面向接口编程，不需要关心底层是哪个交易所
 */
public interface ExchangeApiClient {

    /**
     * 获取当前交易所标识
     */
    ExchangeEnum getExchange();

    /**
     * 获取K线数据
     *
     * @param symbol    交易对 (统一格式: BTC/USDT)
     * @param marketType 市场类型
     * @param interval  K线周期
     * @param startTime 开始时间(ms), 为null表示从最新往前取
     * @param endTime   结束时间(ms), 为null表示到当前
     * @param limit     数量限制
     * @return K线列表
     */
    List<KlineDTO> getKlines(String symbol, MarketType marketType, KlineInterval interval,
                             Long startTime, Long endTime, Integer limit);

    /**
     * 获取最新Tick行情
     *
     * @param symbol    交易对
     * @param marketType 市场类型
     * @return Tick数据
     */
    TickDTO getTicker(String symbol, MarketType marketType);

    /**
     * 批量获取所有交易对Tick
     *
     * @param symbols   交易对列表
     * @param marketType 市场类型
     * @return Tick列表
     */
    List<TickDTO> getTickers(List<String> symbols, MarketType marketType);

    /**
     * 获取深度数据
     *
     * @param symbol    交易对
     * @param marketType 市场类型
     * @param limit     深度档数(5/10/20/50/100)
     * @return 深度数据
     */
    DepthDTO getDepth(String symbol, MarketType marketType, int limit);

    /**
     * 将统一交易对格式转为交易所特定格式
     * 如 BTC/USDT -> BTCUSDT (Binance) 或 BTC-USDT (OKX)
     */
    String convertSymbol(String symbol, MarketType marketType);

    // ===================== 交易接口 =====================

    /**
     * 下单
     *
     * @param symbol      交易对
     * @param marketType  市场类型
     * @param side        BUY/SELL
     * @param positionSide LONG/SHORT (合约专用)
     * @param orderType   MARKET/LIMIT
     * @param price       限价单价格(市价单可为null)
     * @param quantity    数量
     * @return 交易所返回的订单ID
     */
    String placeOrder(String symbol, MarketType marketType, String side, String positionSide,
                      String orderType, String price, String quantity);

    /**
     * 撤单
     */
    boolean cancelOrder(String symbol, MarketType marketType, String orderId);

    /**
     * 查询订单状态
     */
    String getOrderStatus(String symbol, MarketType marketType, String orderId);

    /**
     * 获取账户余额
     *
     * @param asset 币种, 如 USDT
     * @return 可用余额字符串
     */
    String getBalance(String asset);
}
