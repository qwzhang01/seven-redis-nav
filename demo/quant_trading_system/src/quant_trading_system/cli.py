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
@click.option("--commission", default=0.0004, help="手续费率")
@click.option("--slippage", default=0.0001, help="滑点率")
@click.option("--mock", is_flag=True, help="使用模拟数据")
def backtest(
    strategy: str,
    symbol: str,
    timeframe: str,
    start: str,
    end: str,
    capital: float,
    commission: float,
    slippage: float,
    mock: bool,
) -> None:
    """运行回测"""
    # 导入策略模块以触发注册
    import quant_trading_system.strategies  # noqa: F401

    from quant_trading_system.models.market import TimeFrame
    from quant_trading_system.services.backtest.backtest_engine import (
        BacktestConfig,
        BacktestEngine,
    )
    from quant_trading_system.services.market.binance_api import BinanceAPI
    from quant_trading_system.services.strategy.base import get_strategy_class

    click.echo(f"Running backtest for {strategy} on {symbol}")
    click.echo(f"Period: {start} to {end}")
    click.echo(f"Initial capital: {capital}")
    click.echo()

    try:
        # 1. 获取策略类
        click.echo(f"Loading strategy: {strategy}")
        strategy_class = get_strategy_class(strategy)
        if not strategy_class:
            click.echo(f"Error: Strategy '{strategy}' not found", err=True)
            click.echo("Available strategies:")
            from quant_trading_system.services.strategy.base import list_strategies
            for name in list_strategies():
                click.echo(f"  - {name}")
            return

        # 2. 解析时间周期
        timeframe_map = {
            "1m": TimeFrame.M1,
            "5m": TimeFrame.M5,
            "15m": TimeFrame.M15,
            "30m": TimeFrame.M30,
            "1h": TimeFrame.H1,
            "4h": TimeFrame.H4,
            "1d": TimeFrame.D1,
            "1w": TimeFrame.W1,
        }
        tf = timeframe_map.get(timeframe.lower())
        if not tf:
            click.echo(f"Error: Invalid timeframe '{timeframe}'", err=True)
            click.echo(f"Supported: {', '.join(timeframe_map.keys())}")
            return

        # 3. 获取历史数据
        if mock:
            click.echo(f"Generating mock data...")
            from quant_trading_system.services.market.mock_data import generate_mock_klines

            bars = generate_mock_klines(
                symbol=symbol,
                timeframe=tf,
                start_time=start,
                end_time=end,
            )
        else:
            click.echo(f"Fetching historical data from Binance...")
            from quant_trading_system.services.market.binance_api import BinanceAPI

            with BinanceAPI(market_type="spot") as api:
                bars = api.fetch_klines(
                    symbol=symbol,
                    timeframe=tf,
                    start_time=start,
                    end_time=end,
                )

        if len(bars) == 0:
            click.echo("Error: No data fetched", err=True)
            return

        click.echo(f"Fetched {len(bars)} bars")
        click.echo()

        # 4. 创建策略实例
        strategy_instance = strategy_class()

        # 5. 配置回测引擎
        config = BacktestConfig(
            initial_capital=capital,
            commission_rate=commission,
            slippage_rate=slippage,
        )

        # 6. 运行回测
        click.echo("Running backtest...")
        engine = BacktestEngine(config=config)
        result = engine.run(strategy_instance, bars)

        # 7. 显示结果
        click.echo()
        click.echo("=" * 60)
        click.echo("Backtest Results")
        click.echo("=" * 60)
        click.echo()

        click.echo("基本信息:")
        click.echo(f"  策略名称: {result.strategy_name}")
        click.echo(f"  回测周期: {result.duration_days:.1f} 天")
        click.echo()

        click.echo("收益指标:")
        click.echo(f"  初始资金: {result.initial_capital:,.2f}")
        click.echo(f"  最终资金: {result.final_capital:,.2f}")
        click.echo(f"  总收益率: {result.total_return:.2%}")
        click.echo(f"  年化收益率: {result.annual_return:.2%}")
        click.echo()

        click.echo("风险指标:")
        click.echo(f"  最大回撤: {result.max_drawdown:.2%}")
        click.echo(f"  波动率: {result.volatility:.2%}")
        click.echo(f"  夏普比率: {result.sharpe_ratio:.2f}")
        click.echo(f"  卡玛比率: {result.calmar_ratio:.2f}")
        click.echo()

        click.echo("交易统计:")
        click.echo(f"  总交易次数: {result.total_trades}")
        click.echo(f"  盈利次数: {result.winning_trades}")
        click.echo(f"  亏损次数: {result.losing_trades}")
        click.echo(f"  胜率: {result.win_rate:.2%}")
        click.echo(f"  盈亏比: {result.profit_factor:.2f}")
        click.echo(f"  平均盈利: {result.avg_win:,.2f}")
        click.echo(f"  平均亏损: {result.avg_loss:,.2f}")
        click.echo()

        click.echo("费用统计:")
        click.echo(f"  总手续费: {result.total_commission:,.2f}")
        click.echo(f"  总滑点: {result.total_slippage:,.2f}")
        click.echo()

        click.echo("=" * 60)
        click.echo("Backtest completed successfully!")

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        import traceback
        traceback.print_exc()


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
    # 导入策略模块以触发注册
    import quant_trading_system.strategies  # noqa: F401

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
