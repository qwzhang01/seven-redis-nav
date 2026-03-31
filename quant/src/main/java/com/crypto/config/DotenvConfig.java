package com.crypto.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.PropertySource;

/**
 * .env 文件配置类
 * 启用 .env 文件支持，让 application.yml 可以读取 .env 文件中的环境变量
 * Spring Boot 2.4+ 会自动从 classpath 根目录加载 .env 文件
 */
@Configuration
@PropertySource("classpath:.env")
public class DotenvConfig {
    // Spring Boot 会自动处理 .env 文件中的配置
}