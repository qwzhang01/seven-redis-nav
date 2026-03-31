package com.crypto.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.crypto.entity.AiAnalysisEntity;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.util.List;

@Mapper
public interface AiAnalysisMapper extends BaseMapper<AiAnalysisEntity> {

    @Select("SELECT * FROM t_ai_analysis WHERE executed = FALSE ORDER BY created_at DESC LIMIT #{limit}")
    List<AiAnalysisEntity> getUnexecutedAnalyses(@Param("limit") int limit);

    @Select("SELECT * FROM t_ai_analysis WHERE exchange = #{exchange} AND symbol = #{symbol} " +
            "AND market_type = #{marketType} ORDER BY analysis_time DESC LIMIT 1")
    AiAnalysisEntity getLatestAnalysis(@Param("exchange") String exchange,
                                       @Param("symbol") String symbol,
                                       @Param("marketType") String marketType);
}
