package com.crypto.service;

import com.crypto.entity.KlineEntity;
import com.crypto.entity.TickEntity;
import com.crypto.mapper.DepthMapper;
import com.crypto.mapper.KlineMapper;
import com.crypto.mapper.TickMapper;
import com.crypto.model.dto.DepthDTO;
import com.crypto.model.dto.KlineDTO;
import com.crypto.model.dto.TickDTO;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Spy;
import org.mockito.junit.jupiter.MockitoExtension;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

/**
 * MarketDataService 行情数据持久化服务测试
 */
@ExtendWith(MockitoExtension.class)
class MarketDataServiceTest {

    @Mock
    private KlineMapper klineMapper;

    @Mock
    private TickMapper tickMapper;

    @Mock
    private DepthMapper depthMapper;

    @Spy
    private ObjectMapper objectMapper = new ObjectMapper();

    @InjectMocks
    private MarketDataService marketDataService;

    // ===================== saveKlines =====================

    @Nested
    @DisplayName("saveKlines 保存K线数据")
    class SaveKlinesTest {

        @Test
        @DisplayName("新K线应该被插入")
        void shouldInsertNewKline() {
            KlineDTO dto = KlineDTO.builder()
                    .exchange("BINANCE")
                    .symbol("BTC/USDT")
                    .marketType("SPOT")
                    .interval("1h")
                    .openTime(1700000000000L)
                    .closeTime(1700003600000L)
                    .openPrice(new BigDecimal("50000"))
                    .highPrice(new BigDecimal("51000"))
                    .lowPrice(new BigDecimal("49000"))
                    .closePrice(new BigDecimal("50500"))
                    .volume(new BigDecimal("100"))
                    .quoteVolume(new BigDecimal("5000000"))
                    .build();

            when(klineMapper.selectOne(any())).thenReturn(null);
            when(klineMapper.insert(any())).thenReturn(1);

            int count = marketDataService.saveKlines(Collections.singletonList(dto));

            assertEquals(1, count);
            verify(klineMapper).insert(any(KlineEntity.class));
        }

        @Test
        @DisplayName("已存在的K线应该被更新")
        void shouldUpdateExistingKline() {
            KlineDTO dto = KlineDTO.builder()
                    .exchange("BINANCE")
                    .symbol("BTC/USDT")
                    .marketType("SPOT")
                    .interval("1h")
                    .openTime(1700000000000L)
                    .closePrice(new BigDecimal("50500"))
                    .highPrice(new BigDecimal("51000"))
                    .lowPrice(new BigDecimal("49000"))
                    .volume(new BigDecimal("200"))
                    .build();

            KlineEntity existing = KlineEntity.builder().id(1L).build();
            when(klineMapper.selectOne(any())).thenReturn(existing);
            when(klineMapper.updateById(any())).thenReturn(1);

            int count = marketDataService.saveKlines(Collections.singletonList(dto));

            assertEquals(0, count); // 更新不计入新增count
            verify(klineMapper).updateById(any(KlineEntity.class));
            verify(klineMapper, never()).insert(any());
        }

        @Test
        @DisplayName("空列表应返回0")
        void emptyListShouldReturnZero() {
            int count = marketDataService.saveKlines(Collections.emptyList());
            assertEquals(0, count);
        }

        @Test
        @DisplayName("多条K线混合新旧数据")
        void shouldHandleMixedNewAndExisting() {
            KlineDTO dto1 = KlineDTO.builder()
                    .exchange("BINANCE").symbol("BTC/USDT").marketType("SPOT")
                    .interval("1h").openTime(1L).closePrice(new BigDecimal("50000"))
                    .build();
            KlineDTO dto2 = KlineDTO.builder()
                    .exchange("BINANCE").symbol("BTC/USDT").marketType("SPOT")
                    .interval("1h").openTime(2L).closePrice(new BigDecimal("51000"))
                    .build();

            when(klineMapper.selectOne(any()))
                    .thenReturn(KlineEntity.builder().id(1L).build())  // 第一条已存在
                    .thenReturn(null);  // 第二条不存在
            when(klineMapper.insert(any())).thenReturn(1);

            int count = marketDataService.saveKlines(Arrays.asList(dto1, dto2));
            assertEquals(1, count);
        }

        @Test
        @DisplayName("null字段应使用默认值")
        void nullFieldsShouldUseDefaults() {
            KlineDTO dto = KlineDTO.builder()
                    .exchange("BINANCE").symbol("BTC/USDT").marketType("SPOT")
                    .interval("1h").openTime(1L)
                    .openPrice(new BigDecimal("50000"))
                    .closePrice(new BigDecimal("50500"))
                    // tradesCount, takerBuyVolume, takerBuyQuoteVolume 为null
                    .build();

            when(klineMapper.selectOne(any())).thenReturn(null);
            when(klineMapper.insert(any())).thenReturn(1);

            ArgumentCaptor<KlineEntity> captor = ArgumentCaptor.forClass(KlineEntity.class);
            marketDataService.saveKlines(Collections.singletonList(dto));
            verify(klineMapper).insert(captor.capture());

            KlineEntity saved = captor.getValue();
            assertEquals(0, saved.getTradesCount());
            assertEquals(BigDecimal.ZERO, saved.getTakerBuyVol());
            assertEquals(BigDecimal.ZERO, saved.getTakerBuyQuote());
        }
    }

    // ===================== saveTick =====================

    @Nested
    @DisplayName("saveTick 保存Tick数据")
    class SaveTickTest {

        @Test
        @DisplayName("正常保存Tick")
        void shouldSaveTick() {
            TickDTO dto = TickDTO.builder()
                    .exchange("BINANCE")
                    .symbol("BTC/USDT")
                    .marketType("SPOT")
                    .lastPrice(new BigDecimal("50000"))
                    .bestBidPrice(new BigDecimal("49999"))
                    .bestAskPrice(new BigDecimal("50001"))
                    .volume24h(new BigDecimal("10000"))
                    .eventTime(System.currentTimeMillis())
                    .build();

            when(tickMapper.insert(any())).thenReturn(1);

            marketDataService.saveTick(dto);

            verify(tickMapper).insert(any(TickEntity.class));
        }

        @Test
        @DisplayName("null DTO 不应插入")
        void nullDtoShouldNotInsert() {
            marketDataService.saveTick(null);
            verify(tickMapper, never()).insert(any());
        }
    }

    // ===================== saveDepth =====================

    @Nested
    @DisplayName("saveDepth 保存深度数据")
    class SaveDepthTest {

        @Test
        @DisplayName("正常保存深度数据（含JSON序列化）")
        void shouldSaveDepthWithJsonSerialization() {
            List<BigDecimal[]> bids = new ArrayList<>();
            bids.add(new BigDecimal[]{new BigDecimal("50000"), new BigDecimal("1.5")});
            bids.add(new BigDecimal[]{new BigDecimal("49999"), new BigDecimal("2.0")});

            List<BigDecimal[]> asks = new ArrayList<>();
            asks.add(new BigDecimal[]{new BigDecimal("50001"), new BigDecimal("1.0")});

            DepthDTO dto = DepthDTO.builder()
                    .exchange("BINANCE")
                    .symbol("BTC/USDT")
                    .marketType("SPOT")
                    .bids(bids)
                    .asks(asks)
                    .lastUpdateId(12345L)
                    .eventTime(System.currentTimeMillis())
                    .build();

            when(depthMapper.insert(any())).thenReturn(1);

            marketDataService.saveDepth(dto);

            verify(depthMapper).insert(any());
        }

        @Test
        @DisplayName("null DTO 不应插入")
        void nullDtoShouldNotInsert() {
            marketDataService.saveDepth(null);
            verify(depthMapper, never()).insert(any());
        }
    }

    // ===================== 查询方法 =====================

    @Nested
    @DisplayName("查询方法")
    class QueryTest {

        @Test
        @DisplayName("getLatestKlineOpenTime 委托给mapper")
        void getLatestKlineOpenTimeShouldDelegateToMapper() {
            when(klineMapper.getLatestOpenTime("BINANCE", "BTC/USDT", "SPOT", "1h"))
                    .thenReturn(1700000000000L);

            Long result = marketDataService.getLatestKlineOpenTime("BINANCE", "BTC/USDT", "SPOT", "1h");
            assertEquals(1700000000000L, result);
        }

        @Test
        @DisplayName("getLatestKlines 委托给mapper")
        void getLatestKlinesShouldDelegateToMapper() {
            List<KlineEntity> mockKlines = Collections.singletonList(
                    KlineEntity.builder().id(1L).build());
            when(klineMapper.getLatestKlines("BINANCE", "BTC/USDT", "SPOT", "1h", 100))
                    .thenReturn(mockKlines);

            List<KlineEntity> result = marketDataService.getLatestKlines("BINANCE", "BTC/USDT", "SPOT", "1h", 100);
            assertEquals(1, result.size());
        }
    }
}
