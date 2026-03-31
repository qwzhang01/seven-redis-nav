package com.crypto.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.crypto.entity.PositionEntity;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.util.List;

@Mapper
public interface PositionMapper extends BaseMapper<PositionEntity> {

    @Select("SELECT * FROM t_position WHERE exchange = #{exchange} AND symbol = #{symbol} " +
            "AND market_type = #{marketType} AND position_side = #{positionSide} AND status = 'OPEN'")
    PositionEntity getOpenPosition(@Param("exchange") String exchange,
                                   @Param("symbol") String symbol,
                                   @Param("marketType") String marketType,
                                   @Param("positionSide") String positionSide);

    @Select("SELECT * FROM t_position WHERE status = 'OPEN'")
    List<PositionEntity> getAllOpenPositions();

    @Select("SELECT COUNT(*) FROM t_position WHERE status = 'OPEN'")
    int countOpenPositions();
}
