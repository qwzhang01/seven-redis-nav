package com.crypto.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.crypto.entity.KlineEntity;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.util.List;

@Mapper
public interface KlineMapper extends BaseMapper<KlineEntity> {

    @Select("SELECT * FROM t_kline WHERE exchange = #{exchange} AND symbol = #{symbol} " +
            "AND market_type = #{marketType} AND interval_val = #{interval} " +
            "AND open_time >= #{startTime} ORDER BY open_time ASC LIMIT #{limit}")
    List<KlineEntity> queryKlines(@Param("exchange") String exchange,
                                  @Param("symbol") String symbol,
                                  @Param("marketType") String marketType,
                                  @Param("interval") String interval,
                                  @Param("startTime") Long startTime,
                                  @Param("limit") int limit);

    @Select("SELECT MAX(open_time) FROM t_kline WHERE exchange = #{exchange} " +
            "AND symbol = #{symbol} AND market_type = #{marketType} AND interval_val = #{interval}")
    Long getLatestOpenTime(@Param("exchange") String exchange,
                           @Param("symbol") String symbol,
                           @Param("marketType") String marketType,
                           @Param("interval") String interval);

    @Select("SELECT * FROM t_kline WHERE exchange = #{exchange} AND symbol = #{symbol} " +
            "AND market_type = #{marketType} AND interval_val = #{interval} " +
            "ORDER BY open_time DESC LIMIT #{limit}")
    List<KlineEntity> getLatestKlines(@Param("exchange") String exchange,
                                      @Param("symbol") String symbol,
                                      @Param("marketType") String marketType,
                                      @Param("interval") String interval,
                                      @Param("limit") int limit);
}
