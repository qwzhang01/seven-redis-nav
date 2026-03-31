package com.crypto.model.vo;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

/**
 * 统一API响应体测试
 */
class ApiResultTest {

    @Test
    @DisplayName("success(data) 返回200和正确数据")
    void successWithDataShouldWork() {
        String data = "hello";
        ApiResult<String> result = ApiResult.success(data);

        assertEquals(200, result.getCode());
        assertEquals("success", result.getMessage());
        assertEquals("hello", result.getData());
        assertTrue(result.getTimestamp() > 0);
    }

    @Test
    @DisplayName("success() 无数据返回200")
    void successWithoutDataShouldWork() {
        ApiResult<Void> result = ApiResult.success();

        assertEquals(200, result.getCode());
        assertEquals("success", result.getMessage());
        assertNull(result.getData());
        assertTrue(result.getTimestamp() > 0);
    }

    @Test
    @DisplayName("error(code, message) 返回指定错误码和消息")
    void errorWithCodeShouldWork() {
        ApiResult<Void> result = ApiResult.error(400, "参数错误");

        assertEquals(400, result.getCode());
        assertEquals("参数错误", result.getMessage());
        assertNull(result.getData());
        assertTrue(result.getTimestamp() > 0);
    }

    @Test
    @DisplayName("error(message) 默认返回500")
    void errorWithMessageOnlyShouldReturn500() {
        ApiResult<Void> result = ApiResult.error("系统异常");

        assertEquals(500, result.getCode());
        assertEquals("系统异常", result.getMessage());
        assertNull(result.getData());
    }

    @Test
    @DisplayName("timestamp 应接近当前时间")
    void timestampShouldBeRecent() {
        long before = System.currentTimeMillis();
        ApiResult<String> result = ApiResult.success("test");
        long after = System.currentTimeMillis();

        assertTrue(result.getTimestamp() >= before);
        assertTrue(result.getTimestamp() <= after);
    }

    @Test
    @DisplayName("泛型支持复杂类型")
    void shouldSupportGenericTypes() {
        ApiResult<Integer> intResult = ApiResult.success(42);
        assertEquals(42, intResult.getData());

        ApiResult<Double> doubleResult = ApiResult.success(3.14);
        assertEquals(3.14, doubleResult.getData());
    }

    @Test
    @DisplayName("Builder 模式正常工作")
    void builderShouldWork() {
        ApiResult<String> result = ApiResult.<String>builder()
                .code(201)
                .message("created")
                .data("new resource")
                .timestamp(12345L)
                .build();

        assertEquals(201, result.getCode());
        assertEquals("created", result.getMessage());
        assertEquals("new resource", result.getData());
        assertEquals(12345L, result.getTimestamp());
    }

    @Test
    @DisplayName("无参构造器正常工作")
    void noArgConstructorShouldWork() {
        ApiResult<String> result = new ApiResult<>();
        assertEquals(0, result.getCode());
        assertNull(result.getMessage());
        assertNull(result.getData());
    }
}
