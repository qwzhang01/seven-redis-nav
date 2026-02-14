import type { Strategy, Signal, Position } from '@/types'

const marketTypes = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'XRP/USDT', 'ADA/USDT', 'DOGE/USDT', 'DOT/USDT']
const strategyTypes = ['网格交易', '趋势跟踪', '均值回归', '动量突破', '套利策略', '马丁格尔', 'DCA定投', '波段交易']
const platforms = ['Binance', 'OKX', 'Bybit', 'Bitget', 'Gate.io']
const riskLevels: Array<'low' | 'medium' | 'high'> = ['low', 'medium', 'high']
const exchanges = ['Binance', 'OKX', 'Bybit', 'Bitget', 'Gate.io', 'Huobi', 'Kraken', 'Coinbase']
const timeframes = ['1m', '5m', '15m', '1h', '4h', '1d', '1w']

function randomFloat(min: number, max: number, decimals = 2): number {
  return parseFloat((Math.random() * (max - min) + min).toFixed(decimals))
}

function randomInt(min: number, max: number): number {
  return Math.floor(Math.random() * (max - min + 1)) + min
}

function randomPick<T>(arr: T[]): T {
  return arr[Math.floor(Math.random() * arr.length)]
}

function generateReturnCurve(days: number, finalReturn: number): { data: number[], labels: string[] } {
  const data: number[] = [0]
  const labels: string[] = []
  const step = finalReturn / days
  
  // 生成起始日期（当前日期往前推days天）
  const startDate = new Date()
  startDate.setDate(startDate.getDate() - days)
  
  for (let i = 1; i <= Math.min(days, 90); i++) {
    const noise = (Math.random() - 0.4) * Math.abs(step) * 3
    data.push(parseFloat((data[i - 1] + step + noise).toFixed(2)))
    
    // 生成对应的时间标签
    const currentDate = new Date(startDate)
    currentDate.setDate(startDate.getDate() + i)
    labels.push(currentDate.toISOString().split('T')[0])
  }
  
  return { data, labels }
}

export function generateStrategies(count = 12): Strategy[] {
  return Array.from({ length: count }, (_, i) => {
    const risk = randomPick(riskLevels)
    const returnRate = risk === 'high' ? randomFloat(20, 150) : risk === 'medium' ? randomFloat(8, 50) : randomFloat(2, 20)
    
    return {
      id: `strategy-${i + 1}`,
      name: `${randomPick(strategyTypes)} ${randomPick(marketTypes).split('/')[0]} #${i + 1}`,
      description: `基于${randomPick(['机器学习', '技术指标', '量价分析', '链上数据', '市场情绪'])}的${randomPick(strategyTypes)}策略，适用于${randomPick(['震荡', '趋势', '高波动', '低波动'])}行情。`,
      market: randomPick(marketTypes),
      type: randomPick(strategyTypes),
      riskLevel: risk,
      returnRate,
      maxDrawdown: randomFloat(3, risk === 'high' ? 40 : risk === 'medium' ? 20 : 10),
      runDays: randomInt(30, 365),
      status: Math.random() > 0.2 ? 'active' : 'stopped',
      logic: `该策略采用${randomPick(['RSI', 'MACD', 'Bollinger Bands', 'EMA交叉', '成交量加权'])}作为核心信号指标，结合${randomPick(['ATR止损', '动态止盈', '仓位管理', '风险平价'])}模块，在${randomPick(['15分钟', '1小时', '4小时', '日线'])}级别进行交易决策。`,
      riskTip: '本策略存在市场风险，历史表现不代表未来收益。请根据自身风险承受能力谨慎选择。',
      params: [
        { name: 'investment', label: '投入资金(USDT)', type: 'number', default: 1000, description: '策略运行的初始资金', required: true },
        { name: 'leverage', label: '杠杆倍数', type: 'select', default: '1x', options: ['1x', '2x', '3x', '5x', '10x'], description: '交易杠杆设置', required: true },
        { name: 'stopLoss', label: '止损比例(%)', type: 'number', default: 5, description: '单笔交易最大亏损比例', required: true },
        { name: 'takeProfit', label: '止盈比例(%)', type: 'number', default: 10, description: '单笔交易目标盈利比例', required: false },
        { name: 'maxPositionSize', label: '最大仓位(%)', type: 'number', default: 20, description: '单笔交易最大仓位占比', required: true },
        { name: 'trailingStop', label: '移动止损', type: 'boolean', default: false, description: '是否启用移动止损功能', required: false },
      ],
      // 新增详细参数
      exchange: randomPick(exchanges),
      tradingPair: randomPick(marketTypes),
      timeframe: randomPick(timeframes) as any,
      capitalAllocation: {
        initialCapital: randomFloat(1000, 50000),
        maxPositionSize: randomFloat(5, 30),
        riskPerTrade: randomFloat(1, 5),
        rebalancingFrequency: randomPick(['daily', 'weekly', 'monthly']) as any,
      },
      riskManagement: {
        stopLoss: randomFloat(2, 10),
        takeProfit: randomFloat(5, 20),
        trailingStop: Math.random() > 0.5,
        maxConcurrentTrades: randomInt(1, 10),
        dailyLossLimit: randomFloat(2, 10),
        weeklyLossLimit: randomFloat(5, 20),
      },
      advancedSettings: {
        slippageTolerance: randomFloat(0.1, 1),
        commissionRate: randomFloat(0.05, 0.2),
        useMarketOrders: Math.random() > 0.3,
        allowShortSelling: Math.random() > 0.4,
        enableHedging: Math.random() > 0.6,
        backtestPeriod: randomInt(30, 365),
      },
    }
  })
}

export function generateSignals(count = 20): Signal[] {
  return Array.from({ length: count }, (_, i) => {
    const risk = randomPick(riskLevels)
    const cumulativeReturn = risk === 'high' ? randomFloat(-20, 200) : risk === 'medium' ? randomFloat(-10, 80) : risk === 'low' ? randomFloat(0, 30) : 0
    const runDays = randomInt(7, 500)
    const positions: Position[] = Array.from({ length: randomInt(1, 5) }, () => {
      const entry = randomFloat(100, 70000)
      const pnlPct = randomFloat(-15, 30)
      return {
        symbol: randomPick(marketTypes),
        side: Math.random() > 0.5 ? 'long' : 'short',
        amount: randomFloat(0.01, 10, 4),
        entryPrice: entry,
        currentPrice: parseFloat((entry * (1 + pnlPct / 100)).toFixed(2)),
        pnl: randomFloat(-500, 2000),
        pnlPercent: pnlPct,
      }
    })

    const returnCurveData = generateReturnCurve(runDays, cumulativeReturn)

    return {
      id: `signal-${i + 1}`,
      name: `${randomPick(['Alpha', 'Sigma', 'Quant', 'Matrix', 'Nexus', 'Omega', 'Apex', 'Pulse'])} ${randomPick(['Pro', 'Elite', 'Master', 'Prime', 'X'])} #${i + 1}`,
      platform: randomPick(platforms),
      type: Math.random() > 0.4 ? 'live' : 'simulated',
      cumulativeReturn,
      maxDrawdown: randomFloat(2, risk === 'high' ? 45 : 20),
      runDays,
      status: Math.random() > 0.15 ? 'running' : 'stopped',
      followers: randomInt(10, 5000),
      returnCurve: returnCurveData.data,
      returnCurveLabels: returnCurveData.labels,
      positions,
      description: `专注于${randomPick(marketTypes)}的${randomPick(['高频', '中频', '低频', '混合'])}交易信号，采用${randomPick(['AI模型', '多因子', '技术面', '基本面'])}分析。`,
      // 新增详细参数
      exchange: randomPick(exchanges),
      tradingPair: randomPick(marketTypes),
      timeframe: randomPick(timeframes) as any,
      signalFrequency: randomPick(['high', 'medium', 'low']) as any,
      riskParameters: {
        maxPositionSize: randomFloat(5, 25),
        stopLossPercentage: randomFloat(2, 8),
        takeProfitPercentage: randomFloat(5, 15),
        riskRewardRatio: randomFloat(1.5, 3),
        volatilityFilter: Math.random() > 0.3,
      },
      notificationSettings: {
        emailAlerts: Math.random() > 0.2,
        pushNotifications: Math.random() > 0.4,
        telegramBot: Math.random() > 0.6,
        discordWebhook: Math.random() > 0.5,
        alertThreshold: randomFloat(2, 10),
      },
      performanceMetrics: {
        sharpeRatio: randomFloat(0.5, 3),
        winRate: randomFloat(40, 85),
        profitFactor: randomFloat(1.1, 3),
        averageHoldingPeriod: randomFloat(1, 30),
        maxConsecutiveLosses: randomInt(1, 8),
      },
    }
  })
}

export const strategies = generateStrategies()
export const signals = generateSignals()