package com.crypto.config;

import org.springframework.core.env.PropertySource;
import org.springframework.core.io.support.EncodedResource;
import org.springframework.core.io.support.PropertySourceFactory;
import org.springframework.core.io.support.ResourcePropertySource;

import java.io.IOException;

/**
 * 自定义 .env 文件 PropertySource Factory
 * 用于读取 .env 文件中的环境变量配置
 */
public class DotenvPropertySource implements PropertySourceFactory {

    @Override
    public PropertySource<?> createPropertySource(String name, EncodedResource resource) throws IOException {
        return new ResourcePropertySource("dotenv", resource);
    }
}