package com.crypto.exchange;

import com.crypto.config.ExchangeProperties;
import com.crypto.enums.ExchangeEnum;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import javax.annotation.PostConstruct;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;

/**
 * 交易所门面工厂 - 门面模式的核心
 * 调用方通过本工厂获取交易所客户端，无需关心底层实现
 */
@Slf4j
@Component
public class ExchangeClientFactory {

    @Autowired
    private List<ExchangeApiClient> exchangeApiClients;

    @Autowired
    private ExchangeProperties exchangeProperties;

    private final Map<ExchangeEnum, ExchangeApiClient> clientMap = new EnumMap<>(ExchangeEnum.class);

    @PostConstruct
    public void init() {
        for (ExchangeApiClient client : exchangeApiClients) {
            clientMap.put(client.getExchange(), client);
            log.info("注册交易所客户端: {}", client.getExchange().getName());
        }
        log.info("共注册 {} 个交易所客户端, 默认交易所: {}",
                clientMap.size(), exchangeProperties.getDefaultExchange());
    }

    /**
     * 获取默认交易所客户端
     */
    public ExchangeApiClient getDefaultClient() {
        ExchangeEnum defaultExchange = ExchangeEnum.fromCode(exchangeProperties.getDefaultExchange());
        return getClient(defaultExchange);
    }

    /**
     * 获取指定交易所客户端
     */
    public ExchangeApiClient getClient(ExchangeEnum exchange) {
        ExchangeApiClient client = clientMap.get(exchange);
        if (client == null) {
            throw new IllegalArgumentException("不支持的交易所: " + exchange);
        }
        return client;
    }

    /**
     * 获取所有已注册的交易所客户端
     */
    public Map<ExchangeEnum, ExchangeApiClient> getAllClients() {
        return clientMap;
    }
}
