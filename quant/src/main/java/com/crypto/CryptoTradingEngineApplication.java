package com.crypto;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.annotation.EnableScheduling;

/**
 * 加密货币量化交易系统启动类
 */
@SpringBootApplication
@EnableScheduling
@EnableAsync
@MapperScan("com.crypto.mapper")
public class CryptoTradingEngineApplication {

    public static void main(String[] args) {
        SpringApplication.run(CryptoTradingEngineApplication.class, args);
    }
}
