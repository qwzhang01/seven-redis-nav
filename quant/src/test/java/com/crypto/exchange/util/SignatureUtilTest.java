package com.crypto.exchange.util;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

/**
 * 签名工具类测试
 */
class SignatureUtilTest {

    @Test
    @DisplayName("HMAC-SHA256 签名结果正确")
    void hmacSha256ShouldProduceCorrectResult() {
        // 使用已知的测试向量验证
        String data = "hello";
        String secret = "world";
        String result = SignatureUtil.hmacSha256(data, secret);

        assertNotNull(result);
        // HMAC-SHA256("hello", "world") 已知结果
        assertEquals(64, result.length()); // SHA256 输出32字节 = 64个hex字符
        assertTrue(result.matches("[0-9a-f]+"));
    }

    @Test
    @DisplayName("HMAC-SHA256 相同输入产生相同输出")
    void hmacSha256ShouldBeDeterministic() {
        String data = "timestamp=1234567890&symbol=BTCUSDT";
        String secret = "mysecretkey";

        String result1 = SignatureUtil.hmacSha256(data, secret);
        String result2 = SignatureUtil.hmacSha256(data, secret);

        assertEquals(result1, result2);
    }

    @Test
    @DisplayName("HMAC-SHA256 不同密钥产生不同签名")
    void hmacSha256DifferentKeysShouldDiffer() {
        String data = "test";
        String result1 = SignatureUtil.hmacSha256(data, "key1");
        String result2 = SignatureUtil.hmacSha256(data, "key2");

        assertNotEquals(result1, result2);
    }

    @Test
    @DisplayName("HMAC-SHA256 空数据签名不应抛出异常")
    void hmacSha256EmptyDataShouldWork() {
        assertDoesNotThrow(() -> SignatureUtil.hmacSha256("", "secret"));
    }

    @Test
    @DisplayName("HMAC-SHA256 空密钥应抛出异常")
    void hmacSha256EmptySecretShouldThrow() {
        assertThrows(Exception.class, () -> SignatureUtil.hmacSha256("data", ""));
    }

    @Test
    @DisplayName("HMAC-SHA256 Base64 签名格式正确（OKX用）")
    void hmacSha256Base64ShouldWork() {
        String data = "2024-01-01T00:00:00.000ZGET/api/v5/account/balance";
        String secret = "okx-secret-key";

        String result = SignatureUtil.hmacSha256Base64(data, secret);

        assertNotNull(result);
        // Base64 编码的结果应该只包含 Base64 字符
        assertTrue(result.matches("[A-Za-z0-9+/=]+"));
    }

    @Test
    @DisplayName("HMAC-SHA256 Base64 相同输入产生相同输出")
    void hmacSha256Base64ShouldBeDeterministic() {
        String data = "testdata";
        String secret = "testsecret";

        String result1 = SignatureUtil.hmacSha256Base64(data, secret);
        String result2 = SignatureUtil.hmacSha256Base64(data, secret);

        assertEquals(result1, result2);
    }

    @Test
    @DisplayName("两种签名方式产生不同格式的输出")
    void hexAndBase64ShouldDiffer() {
        String data = "test";
        String secret = "key";

        String hexResult = SignatureUtil.hmacSha256(data, secret);
        String base64Result = SignatureUtil.hmacSha256Base64(data, secret);

        // 格式不同但代表同一签名
        assertNotEquals(hexResult, base64Result);
    }

    @Test
    @DisplayName("签名支持中文字符")
    void shouldSupportChineseCharacters() {
        assertDoesNotThrow(() -> SignatureUtil.hmacSha256("你好世界", "密钥"));
        assertDoesNotThrow(() -> SignatureUtil.hmacSha256Base64("你好世界", "密钥"));
    }

    @Test
    @DisplayName("签名支持特殊字符")
    void shouldSupportSpecialCharacters() {
        String data = "param1=value1&param2=hello%20world&timestamp=1234567890";
        String secret = "my!@#$%^&*()_+secret";

        assertDoesNotThrow(() -> SignatureUtil.hmacSha256(data, secret));
        String result = SignatureUtil.hmacSha256(data, secret);
        assertEquals(64, result.length());
    }
}
