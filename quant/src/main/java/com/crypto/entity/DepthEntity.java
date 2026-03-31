package com.crypto.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * 深度数据实体
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@TableName("t_depth")
public class DepthEntity {

    @TableId(type = IdType.AUTO)
    private Long id;

    private String exchange;
    private String symbol;
    private String marketType;
    /** 买单JSON */
    private String bids;
    /** 卖单JSON */
    private String asks;
    private Long lastUpdateId;
    private Long eventTime;

    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createdAt;
}
