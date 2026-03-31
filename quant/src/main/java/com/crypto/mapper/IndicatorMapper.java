package com.crypto.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.crypto.entity.IndicatorEntity;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

@Mapper
public interface IndicatorMapper extends BaseMapper<IndicatorEntity> {

    @Select("SELECT * FROM t_indicator WHERE exchange = #{exchange} AND symbol = #{symbol} " +
            "AND market_type = #{marketType} AND interval_val = #{interval} " +
            "ORDER BY calc_time DESC LIMIT 1")
    IndicatorEntity getLatestIndicator(@Param("exchange") String exchange,
                                       @Param("symbol") String symbol,
                                       @Param("marketType") String marketType,
                                       @Param("interval") String interval);
}
