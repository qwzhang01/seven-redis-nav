package com.crypto.exchange;

import com.crypto.config.ExchangeProperties;
import com.crypto.enums.ExchangeEnum;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.Arrays;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.when;

/**
 * ExchangeClientFactory 工厂类测试
 */
@ExtendWith(MockitoExtension.class)
class ExchangeClientFactoryTest {

    @Mock
    private ExchangeApiClient binanceClient;

    @Mock
    private ExchangeApiClient okxClient;

    @Mock
    private ExchangeProperties exchangeProperties;

    private ExchangeClientFactory factory;

    @BeforeEach
    void setUp() {
        when(binanceClient.getExchange()).thenReturn(ExchangeEnum.BINANCE);
        when(okxClient.getExchange()).thenReturn(ExchangeEnum.OKX);

        factory = new ExchangeClientFactory();

        // 通过反射设置私有字段(测试用)
        try {
            java.lang.reflect.Field clientsField = ExchangeClientFactory.class.getDeclaredField("exchangeApiClients");
            clientsField.setAccessible(true);
            clientsField.set(factory, Arrays.asList(binanceClient, okxClient));

            java.lang.reflect.Field propsField = ExchangeClientFactory.class.getDeclaredField("exchangeProperties");
            propsField.setAccessible(true);
            propsField.set(factory, exchangeProperties);
        } catch (Exception e) {
            fail("反射设置字段失败: " + e.getMessage());
        }

        when(exchangeProperties.getDefaultExchange()).thenReturn("BINANCE");
        factory.init();
    }

    @Test
    @DisplayName("getClient 获取已注册的交易所客户端")
    void shouldGetRegisteredClient() {
        ExchangeApiClient client = factory.getClient(ExchangeEnum.BINANCE);
        assertNotNull(client);
        assertEquals(ExchangeEnum.BINANCE, client.getExchange());
    }

    @Test
    @DisplayName("getClient 获取OKX客户端")
    void shouldGetOkxClient() {
        ExchangeApiClient client = factory.getClient(ExchangeEnum.OKX);
        assertNotNull(client);
        assertEquals(ExchangeEnum.OKX, client.getExchange());
    }

    @Test
    @DisplayName("getDefaultClient 返回默认交易所客户端")
    void shouldReturnDefaultClient() {
        ExchangeApiClient client = factory.getDefaultClient();
        assertNotNull(client);
        assertEquals(ExchangeEnum.BINANCE, client.getExchange());
    }

    @Test
    @DisplayName("getAllClients 返回所有注册的客户端")
    void shouldReturnAllClients() {
        Map<ExchangeEnum, ExchangeApiClient> clients = factory.getAllClients();
        assertEquals(2, clients.size());
        assertTrue(clients.containsKey(ExchangeEnum.BINANCE));
        assertTrue(clients.containsKey(ExchangeEnum.OKX));
    }
}
