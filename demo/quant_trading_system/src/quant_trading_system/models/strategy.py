"""
策略模块数据库模型
=================

定义系统预设策略相关的 SQLAlchemy ORM 模型，包括：
- PresetStrategy: 系统预设策略主表
- UserStrategy: 用户策略实例表（实盘/模拟）
- SimulationTrade: 模拟交易记录表
- SimulationPosition: 模拟持仓表
- SimulationLog: 模拟运行日志表
"""

from datetime import datetime

from sqlalchemy import (
    Column, String, Boolean, DateTime, Text, Integer, BigInteger, Numeric, )
from sqlalchemy.dialects.postgresql import JSONB

from quant_trading_system.core.snowflake import generate_snowflake_id
from quant_trading_system.models.base import Base


class PresetStrategy(Base):
    """
    系统预设策略表

    由管理员在 M 端创建和管理，C 端用户可浏览、查看详情并基于此创建策略实例。
    """
    __tablename__ = "preset_strategies"

    id = Column(BigInteger, primary_key=True, default=generate_snowflake_id)
    name = Column(String(128), nullable=False, comment="策略名称")
    description = Column(Text, comment="策略简要说明")
    detail = Column(Text, comment="策略详细介绍")
    strategy_type = Column(String(32), nullable=False,
                           comment="策略类型: grid/trend/mean_reversion等")
    market_type = Column(String(16), nullable=False, default="spot",
                         comment="市场类型: spot/futures/margin")
    risk_level = Column(String(16), nullable=False, default="medium",
                        comment="风险等级: low/medium/high")
    exchange = Column(String(32), default="binance", comment="交易所")
    symbols = Column(JSONB, comment="适用交易对列表")
    timeframe = Column(String(8), default="1h", comment="默认K线周期")

    # 策略逻辑相关
    logic_description = Column(Text, comment="策略逻辑说明")
    params_schema = Column(JSONB, comment="可配置参数 schema（JSON Schema格式）")
    default_params = Column(JSONB, comment="默认策略参数")
    risk_params = Column(JSONB, comment="风险管理参数（止损/止盈/移动止损等）")
    advanced_params = Column(JSONB, comment="高级参数（滑点/手续费/做空等）")
    risk_warning = Column(Text, comment="风险提示")

    # 表现统计（回测或历史运行数据）
    total_return = Column(Numeric(10, 6), comment="累计收益率")
    max_drawdown = Column(Numeric(10, 6), comment="最大回撤")
    sharpe_ratio = Column(Numeric(10, 6), comment="夏普比率")
    win_rate = Column(Numeric(10, 6), comment="胜率")
    running_days = Column(Integer, default=0, comment="运行天数")

    # 状态管理
    status = Column(String(16), default="draft",
                    comment="策略状态: draft/testing/running/paused/stopped/error")
    is_published = Column(Boolean, default=False, comment="是否已上架（对C端可见）")
    is_featured = Column(Boolean, default=False, comment="是否推荐（首页展示）")
    sort_order = Column(Integer, default=0, comment="排序权重")

    # 审计字段
    create_by = Column(String(64), default="system")
    create_time = Column(DateTime, default=datetime.utcnow)
    update_by = Column(String(64))
    update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    enable_flag = Column(Boolean, default=True, comment="逻辑删除标识")


class UserStrategy(Base):
    """
    用户策略实例表

    用户基于系统预设策略创建的实盘或模拟策略实例。
    """
    __tablename__ = "user_strategies"

    id = Column(BigInteger, primary_key=True, default=generate_snowflake_id)
    user_id = Column(BigInteger, nullable=False, comment="用户ID")
    preset_strategy_id = Column(BigInteger, nullable=False, comment="关联的预设策略ID")
    name = Column(String(128), nullable=False, comment="用户自定义策略名称")
    mode = Column(String(16), nullable=False, default="live",
                  comment="运行模式: live/simulate")

    # 策略配置
    exchange = Column(String(32), default="binance", comment="交易所")
    symbols = Column(JSONB, comment="交易对列表")
    timeframe = Column(String(8), default="1h", comment="K线周期")
    leverage = Column(Integer, default=1, comment="杠杆倍数")
    initial_capital = Column(Numeric(20, 2), default=10000, comment="初始资金(USDT)")
    params = Column(JSONB, comment="用户自定义策略参数")

    # 仓位控制
    trade_mode = Column(String(16), default="both",
                        comment="开仓模式: both/long_only/short_only")
    take_profit = Column(Numeric(10, 6), comment="止盈百分比")
    stop_loss = Column(Numeric(10, 6), comment="止损百分比")
    stop_mode = Column(String(16), default="both",
                       comment="止盈止损模式: both/tp_only/sl_only")
    max_positions = Column(Integer, default=10, comment="最大持仓数")
    max_orders = Column(Integer, default=50, comment="最大订单数")

    # 高级设置
    max_consecutive_losses = Column(Integer, comment="最大连续亏损次数")
    auto_cancel_orders = Column(Boolean, default=False, comment="自动撤单")
    auto_close_reverse = Column(Boolean, default=False, comment="自动平反向仓")
    reverse_open = Column(Boolean, default=False, comment="反向开仓")

    # 运行时间控制
    running_days = Column(JSONB, comment="运行星期列表 [1,2,3,4,5]")
    running_time_start = Column(String(8), comment="每日运行开始时间 HH:MM")
    running_time_end = Column(String(8), comment="每日运行结束时间 HH:MM")

    # 筛选器配置
    filters = Column(JSONB, comment="筛选器列表")

    # 运行状态
    status = Column(String(16), default="stopped",
                    comment="策略状态: draft/running/paused/stopped/error")

    # 表现统计
    current_value = Column(Numeric(20, 2), comment="当前净值(USDT)")
    total_return = Column(Numeric(10, 6), default=0, comment="总收益率")
    today_return = Column(Numeric(10, 6), default=0, comment="今日收益率")
    max_drawdown = Column(Numeric(10, 6), default=0, comment="最大回撤")
    sharpe_ratio = Column(Numeric(10, 6), comment="夏普比率")
    calmar_ratio = Column(Numeric(10, 6), comment="卡玛比率")
    sortino_ratio = Column(Numeric(10, 6), comment="索提诺比率")
    win_rate = Column(Numeric(10, 6), default=0, comment="胜率")
    total_trades = Column(Integer, default=0, comment="总交易次数")
    signal_count = Column(Integer, default=0, comment="信号数量")
    var_value = Column(Numeric(10, 6), comment="VaR风险价值")
    volatility = Column(Numeric(10, 6), comment="波动率")

    # 运行时间记录
    started_at = Column(DateTime, comment="最近启动时间")
    stopped_at = Column(DateTime, comment="最近停止时间")

    # 审计字段
    create_by = Column(String(64))
    create_time = Column(DateTime, default=datetime.utcnow)
    update_by = Column(String(64))
    update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    enable_flag = Column(Boolean, default=True, comment="逻辑删除标识")


class SimulationTrade(Base):
    """
    模拟交易记录表
    """
    __tablename__ = "simulation_trades"

    id = Column(BigInteger, primary_key=True, default=generate_snowflake_id)
    user_strategy_id = Column(BigInteger, nullable=False, comment="关联的用户策略ID")
    symbol = Column(String(32), nullable=False, comment="交易对")
    side = Column(String(16), nullable=False, comment="交易方向: buy/sell")
    price = Column(Numeric(20, 8), nullable=False, comment="成交价格")
    amount = Column(Numeric(20, 8), nullable=False, comment="成交数量")
    value = Column(Numeric(20, 8), comment="成交额(USDT)")
    fee = Column(Numeric(20, 8), default=0, comment="手续费")
    pnl = Column(Numeric(20, 8), comment="盈亏金额(USDT)")
    trade_time = Column(DateTime, default=datetime.utcnow, comment="成交时间")
    create_time = Column(DateTime, default=datetime.utcnow)


class SimulationPosition(Base):
    """
    模拟持仓表
    """
    __tablename__ = "simulation_positions"

    id = Column(BigInteger, primary_key=True, default=generate_snowflake_id)
    user_strategy_id = Column(BigInteger, nullable=False, comment="关联的用户策略ID")
    symbol = Column(String(32), nullable=False, comment="交易对")
    direction = Column(String(8), nullable=False, comment="持仓方向: long/short")
    amount = Column(Numeric(20, 8), nullable=False, comment="持仓数量")
    entry_price = Column(Numeric(20, 8), nullable=False, comment="入场价格")
    current_price = Column(Numeric(20, 8), comment="当前价格")
    pnl = Column(Numeric(20, 8), default=0, comment="盈亏金额(USDT)")
    pnl_ratio = Column(Numeric(10, 6), default=0, comment="盈亏比例")
    status = Column(String(16), default="open", comment="持仓状态: open/closed")
    open_time = Column(DateTime, default=datetime.utcnow, comment="开仓时间")
    close_time = Column(DateTime, comment="平仓时间")
    create_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SimulationLog(Base):
    """
    模拟运行日志表
    """
    __tablename__ = "simulation_logs"

    id = Column(BigInteger, primary_key=True, default=generate_snowflake_id)
    user_strategy_id = Column(BigInteger, nullable=False, comment="关联的用户策略ID")
    level = Column(String(16), default="info",
                   comment="日志级别: info/warn/error/trade")
    message = Column(Text, nullable=False, comment="日志内容")
    log_time = Column(DateTime, default=datetime.utcnow, comment="日志时间")
    create_time = Column(DateTime, default=datetime.utcnow)
