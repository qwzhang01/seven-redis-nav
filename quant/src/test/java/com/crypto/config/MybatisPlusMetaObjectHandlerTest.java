package com.crypto.config;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

/**
 * MybatisPlusMetaObjectHandler 字段自动填充测试
 * 由于 MetaObject 与 MyBatis-Plus 深度绑定，
 * 这里主要验证 handler 实例可以正常创建
 */
class MybatisPlusMetaObjectHandlerTest {

    @Test
    @DisplayName("handler 实例可以正常创建")
    void shouldCreateInstance() {
        MybatisPlusMetaObjectHandler handler = new MybatisPlusMetaObjectHandler();
        assertNotNull(handler);
    }

    @Test
    @DisplayName("handler 实现了 MetaObjectHandler 接口")
    void shouldImplementMetaObjectHandler() {
        MybatisPlusMetaObjectHandler handler = new MybatisPlusMetaObjectHandler();
        assertTrue(handler instanceof com.baomidou.mybatisplus.core.handlers.MetaObjectHandler);
    }
}
