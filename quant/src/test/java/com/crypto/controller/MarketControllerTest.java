package com.crypto.controller;

import com.crypto.controller.GlobalExceptionHandler;
import com.crypto.entity.AiAnalysisEntity;
import com.crypto.entity.KlineEntity;
import com.crypto.enums.ExchangeEnum;
import com.crypto.exchange.ExchangeApiClient;
import com.crypto.exchange.ExchangeClientFactory;
import com.crypto.model.dto.DepthDTO;
import com.crypto.model.dto.KlineDTO;
import com.crypto.model.dto.TickDTO;
import com.crypto.service.MarketDataService;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.test.context.ContextConfiguration;
import org.springframework.test.web.servlet.MockMvc;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;

import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/**
 * MarketController 行情API测试
 */
@WebMvcTest
@ContextConfiguration(classes = {MarketController.class, GlobalExceptionHandler.class})
class MarketControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private ExchangeClientFactory exchangeClientFactory;

    @MockBean
    private MarketDataService marketDataService;

    private ExchangeApiClient mockClient() {
        ExchangeApiClient client = org.mockito.Mockito.mock(ExchangeApiClient.class);
        when(exchangeClientFactory.getClient(any(ExchangeEnum.class))).thenReturn(client);
        return client;
    }

    // ===================== GET /api/market/klines =====================

    @Nested
    @DisplayName("GET /api/market/klines")
    class GetKlinesTest {

        @Test
        @DisplayName("正常获取K线数据")
        void shouldReturnKlines() throws Exception {
            ExchangeApiClient client = mockClient();

            KlineDTO kline = KlineDTO.builder()
                    .exchange("BINANCE")
                    .symbol("BTCUSDT")
                    .openPrice(new BigDecimal("50000"))
                    .closePrice(new BigDecimal("50500"))
                    .highPrice(new BigDecimal("51000"))
                    .lowPrice(new BigDecimal("49500"))
                    .volume(new BigDecimal("100"))
                    .build();
            when(client.getKlines(anyString(), any(), any(), any(), any(), anyInt()))
                    .thenReturn(Collections.singletonList(kline));

            mockMvc.perform(get("/api/market/klines")
                            .param("symbol", "BTC/USDT")
                            .param("exchange", "BINANCE")
                            .param("marketType", "SPOT")
                            .param("interval", "1h")
                            .param("limit", "100"))
                    .andExpect(status().isOk())
                    .andExpect(jsonPath("$.code").value(200))
                    .andExpect(jsonPath("$.data").isArray())
                    .andExpect(jsonPath("$.data[0].openPrice").value(50000));
        }

        @Test
        @DisplayName("缺少必填参数 symbol")
        void shouldReturn400WhenMissingSymbol() throws Exception {
            mockMvc.perform(get("/api/market/klines"))
                    .andExpect(status().isBadRequest());
        }

        @Test
        @DisplayName("返回空列表")
        void shouldReturnEmptyList() throws Exception {
            ExchangeApiClient client = mockClient();
            when(client.getKlines(anyString(), any(), any(), any(), any(), anyInt()))
                    .thenReturn(new ArrayList<>());

            mockMvc.perform(get("/api/market/klines")
                            .param("symbol", "BTC/USDT"))
                    .andExpect(status().isOk())
                    .andExpect(jsonPath("$.code").value(200))
                    .andExpect(jsonPath("$.data").isEmpty());
        }
    }

    // ===================== GET /api/market/klines/history =====================

    @Nested
    @DisplayName("GET /api/market/klines/history")
    class GetHistoryKlinesTest {

        @Test
        @DisplayName("正常获取历史K线")
        void shouldReturnHistoryKlines() throws Exception {
            KlineEntity kline = KlineEntity.builder()
                    .exchange("BINANCE")
                    .symbol("BTC/USDT")
                    .openPrice(new BigDecimal("50000"))
                    .closePrice(new BigDecimal("50500"))
                    .build();
            when(marketDataService.getLatestKlines(anyString(), anyString(), anyString(), anyString(), anyInt()))
                    .thenReturn(Collections.singletonList(kline));

            mockMvc.perform(get("/api/market/klines/history")
                            .param("symbol", "BTC/USDT"))
                    .andExpect(status().isOk())
                    .andExpect(jsonPath("$.code").value(200))
                    .andExpect(jsonPath("$.data").isArray());
        }
    }

    // ===================== GET /api/market/ticker =====================

    @Nested
    @DisplayName("GET /api/market/ticker")
    class GetTickerTest {

        @Test
        @DisplayName("正常获取Tick")
        void shouldReturnTicker() throws Exception {
            ExchangeApiClient client = mockClient();

            TickDTO tick = TickDTO.builder()
                    .exchange("BINANCE")
                    .symbol("BTC/USDT")
                    .lastPrice(new BigDecimal("50000"))
                    .volume24h(new BigDecimal("10000"))
                    .build();
            when(client.getTicker(anyString(), any())).thenReturn(tick);

            mockMvc.perform(get("/api/market/ticker")
                            .param("symbol", "BTC/USDT"))
                    .andExpect(status().isOk())
                    .andExpect(jsonPath("$.code").value(200))
                    .andExpect(jsonPath("$.data.lastPrice").value(50000));
        }
    }

    // ===================== GET /api/market/tickers =====================

    @Nested
    @DisplayName("GET /api/market/tickers")
    class GetTickersTest {

        @Test
        @DisplayName("批量获取Tick")
        void shouldReturnMultipleTickers() throws Exception {
            ExchangeApiClient client = mockClient();

            TickDTO btcTick = TickDTO.builder().symbol("BTC/USDT").lastPrice(new BigDecimal("50000")).build();
            TickDTO ethTick = TickDTO.builder().symbol("ETH/USDT").lastPrice(new BigDecimal("3000")).build();
            when(client.getTickers(anyList(), any())).thenReturn(Arrays.asList(btcTick, ethTick));

            mockMvc.perform(get("/api/market/tickers")
                            .param("symbols", "BTC/USDT,ETH/USDT"))
                    .andExpect(status().isOk())
                    .andExpect(jsonPath("$.code").value(200))
                    .andExpect(jsonPath("$.data").isArray())
                    .andExpect(jsonPath("$.data.length()").value(2));
        }
    }

    // ===================== GET /api/market/depth =====================

    @Nested
    @DisplayName("GET /api/market/depth")
    class GetDepthTest {

        @Test
        @DisplayName("正常获取深度数据")
        void shouldReturnDepth() throws Exception {
            ExchangeApiClient client = mockClient();

            DepthDTO depth = DepthDTO.builder()
                    .exchange("BINANCE")
                    .symbol("BTC/USDT")
                    .bids(new ArrayList<>())
                    .asks(new ArrayList<>())
                    .lastUpdateId(12345L)
                    .build();
            when(client.getDepth(anyString(), any(), anyInt())).thenReturn(depth);

            mockMvc.perform(get("/api/market/depth")
                            .param("symbol", "BTC/USDT"))
                    .andExpect(status().isOk())
                    .andExpect(jsonPath("$.code").value(200))
                    .andExpect(jsonPath("$.data.lastUpdateId").value(12345));
        }
    }

    // ===================== 无效交易所代码 =====================

    @Nested
    @DisplayName("异常场景")
    class ErrorScenarioTest {

        @Test
        @DisplayName("无效的交易所代码应返回400")
        void invalidExchangeShouldReturn400() throws Exception {
            when(exchangeClientFactory.getClient(any()))
                    .thenThrow(new IllegalArgumentException("Unknown exchange: HUOBI"));

            mockMvc.perform(get("/api/market/ticker")
                            .param("symbol", "BTC/USDT")
                            .param("exchange", "HUOBI"))
                    .andExpect(status().isBadRequest());
        }
    }
}
