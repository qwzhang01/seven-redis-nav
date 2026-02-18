"""
测试启动脚本
==========

直接使用uvicorn启动FastAPI应用，用于测试服务器是否能正常启动
"""

import uvicorn

if __name__ == "__main__":
    # 直接启动FastAPI应用
    uvicorn.run(
        "quant_trading_system.api.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
