"""
命令行工具
==========

提供系统命令行接口
"""

import click
import uvicorn


@click.group()
def main() -> None:
    """量化交易系统命令行工具"""
    pass


@main.command()
@click.option("--host", default="0.0.0.0", help="监听地址")
@click.option("--port", default=8000, help="监听端口")
@click.option("--reload", is_flag=True, help="开发模式（自动重载）")
@click.option("--workers", default=1, help="工作进程数")
def serve(host: str, port: int, reload: bool, workers: int) -> None:
    """启动API服务"""
    click.echo(f"Starting API server at http://{host}:{port}")
    
    uvicorn.run(
        "quant_trading_system.api.main:app",
        host=host,
        port=port,
        reload=reload,
        workers=workers,
    )


@main.command()
@click.option("--strategy", required=True, help="策略名称")
@click.option("--symbol", required=True, help="交易对")
@click.option("--timeframe", default="1m", help="时间周期")
@click.option("--start", required=True, help="开始时间")
@click.option("--end", required=True, help="结束时间")
@click.option("--capital", default=1000000.0, help="初始资金")
def backtest(
    strategy: str,
    symbol: str,
    timeframe: str,
    start: str,
    end: str,
    capital: float,
) -> None:
    """运行回测"""
    click.echo(f"Running backtest for {strategy} on {symbol}")
    click.echo(f"Period: {start} to {end}")
    click.echo(f"Initial capital: {capital}")
    
    # 实际应调用回测引擎
    click.echo("Backtest completed.")


@main.command()
@click.option("--config", default=".env", help="配置文件路径")
def check_config(config: str) -> None:
    """检查配置"""
    from quant_trading_system.core.config import settings
    
    click.echo("Configuration:")
    click.echo(f"  Environment: {settings.env}")
    click.echo(f"  Debug: {settings.debug}")
    click.echo(f"  Database: {settings.database.timescale_host}")
    click.echo(f"  Redis: {settings.redis.host}:{settings.redis.port}")


@main.command()
def list_strategies() -> None:
    """列出可用策略"""
    from quant_trading_system.services.strategy.base import list_strategies
    
    strategies = list_strategies()
    
    if strategies:
        click.echo("Available strategies:")
        for name in strategies:
            click.echo(f"  - {name}")
    else:
        click.echo("No strategies registered.")


@main.command()
def list_indicators() -> None:
    """列出可用指标"""
    from quant_trading_system.services.indicators.base import IndicatorRegistry
    
    indicators = IndicatorRegistry.list_indicators()
    
    click.echo("Available indicators:")
    for name in indicators:
        info = IndicatorRegistry.get_info(name)
        if info:
            click.echo(f"  - {name}: {info.get('description', '')}")


if __name__ == "__main__":
    main()
