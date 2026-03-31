package com.crypto.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.crypto.entity.TickEntity;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface TickMapper extends BaseMapper<TickEntity> {
}
