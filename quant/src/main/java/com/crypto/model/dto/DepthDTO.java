package com.crypto.model.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.util.List;

/**
 * 深度数据DTO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DepthDTO {

    private String exchange;
    private String symbol;
    private String marketType;
    /** 买单列表 [[price, qty], ...] */
    private List<BigDecimal[]> bids;
    /** 卖单列表 [[price, qty], ...] */
    private List<BigDecimal[]> asks;
    /** 最后更新ID */
    private Long lastUpdateId;
    /** 事件时间(ms) */
    private Long eventTime;
}
