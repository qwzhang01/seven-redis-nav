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
def serve(
    host: str,
    port: int,
    reload: bool,
    workers: int,
) -> None:
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
    import quant_trading_system.strategy.strategies  # noqa: F401

    from quant_trading_system.core.config import settings
    from quant_trading_system.core.enums import KlineInterval
    from quant_trading_system.services.backtest.backtest_engine import (
        BacktestConfig,
        BacktestEngine,
    )
    from quant_trading_system.strategy import get_strategy_class

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
            from quant_trading_system.strategy import list_strategies
            for name in list_strategies():
                click.echo(f"  - {name}")
            return

        # 2. 解析时间周期
        timeframe_map = {
            "1m": KlineInterval.MIN_1,
            "5m": KlineInterval.MIN_5,
            "15m": KlineInterval.MIN_15,
            "30m": KlineInterval.MIN_30,
            "1h": KlineInterval.HOUR_1,
            "4h": KlineInterval.HOUR_4,
            "1d": KlineInterval.DAY_1,
            "1w": KlineInterval.WEEK_1,
        }
        tf = timeframe_map.get(timeframe.lower())
        if not tf:
            click.echo(f"Error: Invalid timeframe '{timeframe}'", err=True)
            click.echo(f"Supported: {', '.join(timeframe_map.keys())}")
            return

        # 3. 获取历史数据
        if mock:
            click.echo(f"Generating mock data...")
            from quant_trading_system.exchange_adapter.mock.mock_data import (
                generate_mock_klines,
                generate_multi_timeframe_klines,
            )

            # 转换symbol格式：从BTCUSDT转换为BTC/USDT
            symbol_formatted = symbol
            if "/" not in symbol and len(symbol) >= 6:
                # 假设格式为"BTCUSDT"，转换为"BTC/USDT"
                base_symbol = symbol[:-4]
                quote_symbol = symbol[-4:]
                symbol_formatted = f"{base_symbol}/{quote_symbol}"
                click.echo(f"Converted symbol format: {symbol} -> {symbol_formatted}")

            # 检查策略是否需要多周期数据
            strategy_tfs = list(
                strategy_class.timeframes) if strategy_class.timeframes else [tf]
            if len(strategy_tfs) > 1:
                click.echo(
                    f"Multi-timeframe strategy detected: {[t.value for t in strategy_tfs]}")
                tf_bars = generate_multi_timeframe_klines(
                    symbol=symbol_formatted,
                    timeframes=strategy_tfs,
                    start_time=start,
                    end_time=end,
                )
                bars = {symbol_formatted: tf_bars}
                total_bars = sum(len(ba) for ba in tf_bars.values())
                click.echo(
                    f"Generated {total_bars} bars across {len(strategy_tfs)} timeframes")
            else:
                bars = generate_mock_klines(
                    symbol=symbol_formatted,
                    timeframe=tf,
                    start_time=start,
                    end_time=end,
                )
        else:
            click.echo(f"Fetching historical data from Binance...")
            from quant_trading_system.exchange_adapter.binance.binance_rest_client import BinanceRestClient

            strategy_tfs = list(
                strategy_class.timeframes) if strategy_class.timeframes else [tf]
            if len(strategy_tfs) > 1:
                click.echo(
                    f"Multi-timeframe strategy: {[t.value for t in strategy_tfs]}")
                tf_bars = {}
                with BinanceRestClient(market_type="spot", proxy_url=settings.exchange.proxy_url) as api:
                    for stf in strategy_tfs:
                        click.echo(f"  Fetching {stf.value} data...")
                        tf_bars[stf] = api.fetch_klines(
                            symbol=symbol,
                            timeframe=stf,
                            start_time=start,
                            end_time=end,
                        )
                # 转换 symbol 格式
                symbol_formatted = symbol
                if "/" not in symbol and len(symbol) >= 6:
                    base_symbol = symbol[:-4]
                    quote_symbol = symbol[-4:]
                    symbol_formatted = f"{base_symbol}/{quote_symbol}"
                bars = {symbol_formatted: tf_bars}
            else:
                with BinanceRestClient(market_type="spot", proxy_url=settings.exchange.proxy_url) as api:
                    bars = api.fetch_klines(
                        symbol=symbol,
                        timeframe=tf,
                        start_time=start,
                        end_time=end,
                    )

        if isinstance(bars, dict):
            # 多周期格式 {symbol: {tf: BarArray}} — 检查最小周期数据量
            first_sym = next(iter(bars.values()))
            if isinstance(first_sym, dict):
                min_len = min(len(ba) for ba in first_sym.values())
            else:
                min_len = len(bars)
            if min_len == 0:
                click.echo("Error: No data fetched", err=True)
                return
            click.echo(f"Data ready (primary timeframe: {min_len} bars)")
        else:
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
        click.echo()

        # 初始化日志系统，确保回测进度日志可见
        from quant_trading_system.core.logging import setup_logging
        setup_logging(level="INFO", log_format="console")

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
@click.option("--strategy", required=True, help="策略名称")
@click.option("--symbol", required=True, multiple=True, help="交易对（可多次指定）")
@click.option("--exchange", default="binance", help="交易所")
@click.option("--market-type", default="spot", help="市场类型 (spot/futures)")
@click.option("--capital", default=100000.0, help="初始资金（paper 模式）")
@click.option("--api-key", default="", envvar="EXCHANGE_API_KEY", help="交易所 API Key")
@click.option("--api-secret", default="", envvar="EXCHANGE_API_SECRET",
              help="交易所 API Secret")
@click.option("--mode", default="paper", type=click.Choice(["paper", "live"]),
              help="运行模式")
def trade(
    strategy: str,
    symbol: tuple[str, ...],
    exchange: str,
    market_type: str,
    capital: float,
    api_key: str,
    api_secret: str,
    mode: str,
) -> None:
    """启动实盘/模拟交易"""
    import asyncio

    # 导入策略模块以触发注册
    import quant_trading_system.strategy.strategies  # noqa: F401

    from quant_trading_system.strategy import get_strategy_class
    from quant_trading_system.services.trading.orchestrator import TradingOrchestrator

    click.echo(f"{'=' * 60}")
    click.echo(
        f"  Quant Trading System — {'LIVE' if mode == 'live' else 'PAPER'} Trading")
    click.echo(f"{'=' * 60}")
    click.echo()

    # 加载策略
    click.echo(f"Loading strategy: {strategy}")
    strategy_class = get_strategy_class(strategy)
    if not strategy_class:
        click.echo(f"Error: Strategy '{strategy}' not found", err=True)
        from quant_trading_system.strategy import list_strategies
        click.echo("Available strategies:")
        for name in list_strategies():
            click.echo(f"  - {name}")
        return

    symbols = list(symbol)
    click.echo(f"Symbols: {symbols}")
    click.echo(f"Exchange: {exchange} ({market_type})")
    click.echo(f"Mode: {mode}")
    click.echo(f"Capital: {capital:,.2f}")
    if strategy_class.timeframes:
        click.echo(f"Timeframes: {[tf.value for tf in strategy_class.timeframes]}")
    click.echo()

    if mode == "live" and (not api_key or not api_secret):
        click.echo(
            "Warning: Live mode without API keys — orders will be simulated",
            err=True,
        )
        click.echo()

    async def _run() -> None:
        orchestrator = TradingOrchestrator(
            mode=mode,
            exchange=exchange,
            market_type=market_type,
            api_key=api_key,
            api_secret=api_secret,
            initial_capital=capital,
        )

        try:
            await orchestrator.start()

            orchestrator.add_strategy(strategy_class, symbols=symbols)
            await orchestrator.start_all_strategies()
            await orchestrator.subscribe_market()

            click.echo("Trading system is running. Press Ctrl+C to stop.")
            click.echo()

            # 定时输出状态
            while orchestrator.is_running:
                await asyncio.sleep(30)
                stats = orchestrator.stats
                se = stats.get("strategy_engine", {})
                te = stats.get("trading_engine", {})
                click.echo(
                    f"[{mode.upper()}] bars={se.get('bar_count', 0)} "
                    f"signals={se.get('signal_count', 0)} "
                    f"orders={te.get('order_stats', {}).get('total_orders', 0)}"
                )

        except KeyboardInterrupt:
            click.echo()
            click.echo("Shutting down...")
        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            import traceback
            traceback.print_exc()
        finally:
            await orchestrator.stop()
            click.echo("Trading system stopped.")

    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        click.echo("\nStopped.")


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
    import quant_trading_system.strategy.strategies  # noqa: F401

    from quant_trading_system.strategy import list_strategies

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
    from quant_trading_system.indicators.base import IndicatorRegistry

    indicators = IndicatorRegistry.list_indicators()

    click.echo("Available indicators:")
    for name in indicators:
        info = IndicatorRegistry.get_info(name)
        if info:
            click.echo(f"  - {name}: {info.get('description', '')}")


if __name__ == "__main__":
    main()
