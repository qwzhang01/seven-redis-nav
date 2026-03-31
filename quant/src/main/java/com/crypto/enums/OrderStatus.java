package com.crypto.enums;

import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * 订单状态
 */
@Getter
@AllArgsConstructor
public enum OrderStatus {

    CREATED("CREATED", "已创建"),
    SUBMITTED("SUBMITTED", "已提交"),
    PARTIALLY_FILLED("PARTIALLY_FILLED", "部分成交"),
    FILLED("FILLED", "完全成交"),
    CANCELLED("CANCELLED", "已撤销"),
    REJECTED("REJECTED", "已拒绝"),
    EXPIRED("EXPIRED", "已过期");

    private final String code;
    private final String name;

    public static OrderStatus fromCode(String code) {
        for (OrderStatus o : values()) {
            if (o.code.equalsIgnoreCase(code)) {
                return o;
            }
        }
        throw new IllegalArgumentException("Unknown order status: " + code);
    }
}
