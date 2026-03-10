"""
Models package - 按领域拆分的 ORM 模型
"""

# 审计模型
from quant_trading_system.models.audit import (  # noqa: F401
    AuditLog,
    RiskAlert,
)
# 基类
from quant_trading_system.models.base import Base  # noqa: F401
# 跟单模型
from quant_trading_system.models.follow import (  # noqa: F401
    SignalFollowOrder,
    SignalFollowPosition,
    SignalFollowTrade,
    SignalFollowEvent,
    SignalFollowReturnCurve,
    ExchangeCopyAccount,
)
# 排行榜模型
from quant_trading_system.models.leaderboard import (  # noqa: F401
    LeaderboardSnapshot,
)
# 信号模型
from quant_trading_system.models.signal import (  # noqa: F401
    Signal,
    SignalProvider,
    SignalReview,
    SignalReviewLike,
    SignalRiskParameters,
    SignalPerformanceMetrics,
    SignalNotificationSettings,
    SignalPosition,
    SignalTradeRecord,
    SignalMonthlyReturn,
    SignalReturnCurve,
    SignalSubscription,
)
# 策略模型
from quant_trading_system.models.strategy import (  # noqa: F401
    PresetStrategy,
    UserStrategy,
    SimulationTrade,
    SimulationPosition,
    SimulationLog,
)
# 行情订阅 & 同步任务模型（subscription.py）
from quant_trading_system.models.subscription import (  # noqa: F401
    Subscription,
    HistoricalSyncTask,
    SyncTask,
)
# 用户领域模型（user.py）
from quant_trading_system.models.user import (  # noqa: F401
    User,
    Exchange,
    UserExchangeAPI,
)
