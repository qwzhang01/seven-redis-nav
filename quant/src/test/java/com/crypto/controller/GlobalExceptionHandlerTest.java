package com.crypto.controller;

import com.crypto.model.vo.ApiResult;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.web.bind.MissingServletRequestParameterException;

import static org.junit.jupiter.api.Assertions.*;

/**
 * GlobalExceptionHandler 全局异常处理测试
 */
class GlobalExceptionHandlerTest {

    private final GlobalExceptionHandler handler = new GlobalExceptionHandler();

    @Test
    @DisplayName("IllegalArgumentException -> 400")
    void shouldHandle400() {
        ApiResult<Void> result = handler.handleIllegalArgument(
                new IllegalArgumentException("Unknown exchange: HUOBI"));

        assertEquals(400, result.getCode());
        assertEquals("Unknown exchange: HUOBI", result.getMessage());
    }

    @Test
    @DisplayName("MissingServletRequestParameterException -> 400")
    void shouldHandle400MissingParam() throws Exception {
        ApiResult<Void> result = handler.handleMissingParameter(
                new MissingServletRequestParameterException("symbol", "String"));

        assertEquals(400, result.getCode());
        assertTrue(result.getMessage().contains("symbol"));
    }

    @Test
    @DisplayName("RuntimeException -> 500")
    void shouldHandle500Runtime() {
        ApiResult<Void> result = handler.handleRuntime(
                new RuntimeException("数据库连接失败"));

        assertEquals(500, result.getCode());
        assertEquals("数据库连接失败", result.getMessage());
    }

    @Test
    @DisplayName("Exception -> 500 系统内部错误")
    void shouldHandle500Exception() {
        ApiResult<Void> result = handler.handleException(
                new Exception("未知异常"));

        assertEquals(500, result.getCode());
        assertEquals("系统内部错误", result.getMessage());
    }
}
