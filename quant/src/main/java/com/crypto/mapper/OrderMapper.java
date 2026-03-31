package com.crypto.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.crypto.entity.OrderEntity;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface OrderMapper extends BaseMapper<OrderEntity> {
}
