package com.crypto.enums;

import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * 交易动作类型
 */
@Getter
@AllArgsConstructor
public enum ActionType {

    OPEN_LONG("OPEN_LONG", "开多"),
    OPEN_SHORT("OPEN_SHORT", "开空"),
    CLOSE_LONG("CLOSE_LONG", "平多"),
    CLOSE_SHORT("CLOSE_SHORT", "平空"),
    PARTIAL_CLOSE_LONG("PARTIAL_CLOSE_LONG", "部分平多"),
    PARTIAL_CLOSE_SHORT("PARTIAL_CLOSE_SHORT", "部分平空"),
    HOLD("HOLD", "持有不操作");

    private final String code;
    private final String name;

    public static ActionType fromCode(String code) {
        for (ActionType a : values()) {
            if (a.code.equalsIgnoreCase(code)) {
                return a;
            }
        }
        return HOLD;
    }
}
