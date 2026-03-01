# ⚠️ 此文件已废弃（deprecated）
# 原 HistoricalSyncExecutor 的功能已由以下模块替代：
# - historical_data_syncer.py（HistoricalDataSyncer + HistoricalSyncConfig）
# - market_event_bus.py（事件驱动异步存储）
#
# 请勿在新代码中引用此文件。
raise ImportError(
    "historical_sync_executor 模块已废弃。"
    "请使用 historical_data_syncer.HistoricalDataSyncer 替代。"
)
