// 页面切换
function showPage(pageId) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.getElementById(pageId).classList.add('active');
    
    // 更新导航高亮
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
        if (item.dataset.page === pageId) item.classList.add('active');
    });
    
    // 初始化图表
    if (pageId === 'tradingPage' && !window.chartInit) {
        initChart();
        window.chartInit = true;
    }
    
    // 渲染策略卡片
    if (pageId === 'strategyPage') renderStrategyCards();
    
    // 策略详情页初始化图表
    if (pageId === 'strategyDetailPage') {
        setTimeout(() => initDetailCharts(), 100);
    }
    
    // 回测结果页初始化图表
    if (pageId === 'backtestResultPage') {
        setTimeout(() => initResultCharts(), 100);
    }
    
    // 实盘监控页初始化图表
    if (pageId === 'liveMonitorPage') {
        setTimeout(() => initLiveChart(), 100);
    }
    
    // 虚拟账户页初始化图表
    if (pageId === 'virtualAccountPage') {
        setTimeout(() => initPaperEquityChart(), 100);
    }
    
    // 模拟监控页初始化图表
    if (pageId === 'paperMonitorPage') {
        setTimeout(() => initPaperLiveChart(), 100);
    }
    
    // 关闭下拉菜单
    document.getElementById('userDropdown')?.classList.remove('show');
    
    // 更新模拟交易横幅显示
    updatePaperBanner();
}

// Toast提示
function showToast(msg, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    const icons = { success: '✓', error: '✗', warning: '⚠', info: 'ℹ' };
    toast.innerHTML = `<span>${icons[type]}</span><span>${msg}</span>`;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

// 模态框
let modalCallback = null;
function showModal(title, content, needPwd = false) {
    document.getElementById('modalTitle').textContent = title;
    document.getElementById('modalContent').textContent = content;
    document.getElementById('modalInput').style.display = needPwd ? 'block' : 'none';
    document.getElementById('modalOverlay').classList.add('show');
}
function closeModal() {
    document.getElementById('modalOverlay').classList.remove('show');
}
function confirmModal() {
    closeModal();
    showToast('操作成功', 'success');
}

// 用户下拉菜单
function toggleDropdown() {
    document.getElementById('userDropdown')?.classList.toggle('show');
}

// 登录
let loginAttempts = 0;
function handleLogin(e) {
    e.preventDefault();
    const pwd = document.getElementById('loginPassword').value;
    const btn = document.getElementById('loginBtn');
    btn.textContent = '登录中...';
    btn.disabled = true;
    
    setTimeout(() => {
        btn.textContent = '登 录';
        btn.disabled = false;
        if (pwd === 'Password123' || pwd.length >= 6) {
            showToast('登录成功！', 'success');
            setTimeout(() => showPage('tradingPage'), 500);
        } else {
            loginAttempts++;
            if (loginAttempts >= 3) {
                document.getElementById('captchaGroup').style.display = 'block';
                showToast('请输入验证码', 'warning');
            } else {
                showToast('密码错误', 'error');
            }
        }
    }, 1000);
}

// 注册
function handleRegister(e) {
    e.preventDefault();
    showToast('注册成功！', 'success');
    setTimeout(() => showPage('loginPage'), 500);
}

// 验证码
function getVerifyCode(btn) {
    btn.disabled = true;
    let count = 60;
    showToast('验证码已发送', 'success');
    const timer = setInterval(() => {
        count--;
        btn.textContent = `${count}s`;
        if (count <= 0) {
            clearInterval(timer);
            btn.textContent = '获取验证码';
            btn.disabled = false;
        }
    }, 1000);
}

// 密码强度
function checkStrength(input) {
    const pwd = input.value;
    const bar = document.getElementById('strengthBar');
    let strength = 0;
    if (pwd.length >= 8) strength++;
    if (/[a-z]/.test(pwd) && /[A-Z]/.test(pwd)) strength++;
    if (/\d/.test(pwd)) strength++;
    if (/[!@#$%^&*]/.test(pwd)) strength++;
    
    bar.className = 'strength-bar';
    if (strength <= 1) bar.classList.add('weak');
    else if (strength <= 2) bar.classList.add('medium');
    else bar.classList.add('strong');
}

// 交易
let orderSide = 'buy';
function switchSide(side) {
    orderSide = side;
    document.querySelectorAll('.order-tab').forEach(t => {
        t.classList.remove('active');
        if (t.classList.contains(side)) t.classList.add('active');
    });
    const btn = document.getElementById('orderBtn');
    btn.className = `order-submit ${side}`;
    btn.textContent = side === 'buy' ? '买入 BTC' : '卖出 BTC';
}

function setAmt(pct) {
    const balance = 10000;
    const price = 45230.50;
    const amt = (balance * pct / 100 / price).toFixed(6);
    document.getElementById('orderAmt').value = amt;
    calcTotal();
}

function calcTotal() {
    const price = 45230.50;
    const amt = parseFloat(document.getElementById('orderAmt')?.value) || 0;
    const total = price * amt;
    document.getElementById('estTotal').textContent = total.toFixed(2) + ' USDT';
}

function submitOrder() {
    const amt = parseFloat(document.getElementById('orderAmt')?.value);
    if (!amt || amt <= 0) {
        showToast('请输入数量', 'error');
        return;
    }
    const btn = document.getElementById('orderBtn');
    btn.textContent = '提交中...';
    btn.disabled = true;
    setTimeout(() => {
        btn.textContent = orderSide === 'buy' ? '买入 BTC' : '卖出 BTC';
        btn.disabled = false;
        showToast('订单提交成功！', 'success');
    }, 1000);
}

// K线图
function initChart() {
    const container = document.getElementById('chartContainer');
    if (!container || !window.LightweightCharts) return;
    
    const chart = LightweightCharts.createChart(container, {
        width: container.clientWidth,
        height: 450,
        layout: { background: { color: '#0d1117' }, textColor: 'rgba(255,255,255,0.6)' },
        grid: { vertLines: { color: '#21262d' }, horzLines: { color: '#21262d' } },
        crosshair: { mode: LightweightCharts.CrosshairMode.Normal },
        rightPriceScale: { borderColor: '#30363d' },
        timeScale: { borderColor: '#30363d', timeVisible: true }
    });
    
    const series = chart.addCandlestickSeries({
        upColor: '#00A870', downColor: '#E34D59',
        borderUpColor: '#00A870', borderDownColor: '#E34D59',
        wickUpColor: '#00A870', wickDownColor: '#E34D59'
    });
    
    // 生成数据
    const data = [];
    let price = 45000;
    const now = Math.floor(Date.now() / 1000);
    for (let i = 200; i >= 0; i--) {
        const time = now - i * 3600;
        const open = price + (Math.random() - 0.5) * 500;
        const close = open + (Math.random() - 0.5) * 400;
        const high = Math.max(open, close) + Math.random() * 200;
        const low = Math.min(open, close) - Math.random() * 200;
        data.push({ time, open, high, low, close });
        price = close;
    }
    series.setData(data);
    
    // 实时更新
    setInterval(() => {
        const last = data[data.length - 1];
        const newPrice = last.close + (Math.random() - 0.5) * 100;
        series.update({
            time: last.time,
            open: last.open,
            high: Math.max(last.high, newPrice),
            low: Math.min(last.low, newPrice),
            close: newPrice
        });
    }, 2000);
    
    window.addEventListener('resize', () => chart.applyOptions({ width: container.clientWidth }));
}

// 策略卡片
const strategies = [
    { name: '双均线趋势跟踪', type: '趋势跟踪', ret: 25.6, dd: -8.2, risk: 'medium', subs: 1234, subscribed: false, fav: false },
    { name: 'BTC网格交易', type: '网格交易', ret: 12.3, dd: -3.5, risk: 'low', subs: 3456, subscribed: true, fav: true },
    { name: 'ETH突破策略', type: '趋势跟踪', ret: 18.9, dd: -12.1, risk: 'high', subs: 892, subscribed: false, fav: false },
    { name: '稳定币套利', type: '套利', ret: 8.5, dd: -1.2, risk: 'low', subs: 5678, subscribed: false, fav: false },
    { name: '波动率做多', type: '趋势跟踪', ret: -5.3, dd: -15.8, risk: 'high', subs: 234, subscribed: false, fav: false },
    { name: '震荡区间策略', type: '网格交易', ret: 15.2, dd: -6.5, risk: 'medium', subs: 1567, subscribed: false, fav: true }
];

function renderStrategyCards() {
    const grid = document.getElementById('strategyGrid');
    if (!grid) return;
    
    const riskText = { low: '🟢 低风险', medium: '🟡 中风险', high: '🔴 高风险' };
    grid.innerHTML = strategies.map((s, i) => `
        <div class="strategy-card" onclick="viewStrategy(${i})">
            <div class="card-header">
                <div class="strategy-icon">🤖</div>
                <div><div class="name">${s.name}</div><div class="type">${s.type}</div></div>
            </div>
            <div class="card-stats">
                <div class="stat"><div class="value ${s.ret >= 0 ? 'positive' : 'negative'}">${s.ret >= 0 ? '+' : ''}${s.ret}%</div><div class="label">近30天收益</div></div>
                <div class="stat"><div class="value negative">${s.dd}%</div><div class="label">最大回撤</div></div>
            </div>
            <div class="card-footer">
                <span class="risk-tag ${s.risk}">${riskText[s.risk]}</span>
                <span>${s.subs.toLocaleString()} 人订阅</span>
            </div>
            <div class="strategy-actions" onclick="event.stopPropagation()">
                <button class="favorite-btn ${s.fav ? 'active' : ''}" onclick="toggleFav(${i})">${s.fav ? '★' : '☆'} 收藏</button>
                <button class="subscribe-btn ${s.subscribed ? 'subscribed' : ''}" onclick="toggleSub(${i})">${s.subscribed ? '✓ 已订阅' : '订阅策略'}</button>
            </div>
        </div>
    `).join('');
}

function viewStrategy(i) {
    const s = strategies[i];
    document.getElementById('detailName').textContent = s.name;
    document.getElementById('detailTitle').textContent = s.name + '策略';
    currentStrategy = s;
    showPage('strategyDetailPage');
    // 重置到第一个Tab
    switchDetailTab('intro');
}

// 当前选中的策略
let currentStrategy = strategies[0];
let detailFav = false;

// 策略详情Tab切换
function switchDetailTab(tab) {
    // 切换Tab高亮
    document.querySelectorAll('#detailTabs span').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('#detailTabs span').forEach(t => {
        if ((tab === 'intro' && t.textContent === '策略说明') ||
            (tab === 'performance' && t.textContent === '绩效分析') ||
            (tab === 'backtest' && t.textContent === '回测报告') ||
            (tab === 'review' && t.textContent === '用户评价')) {
            t.classList.add('active');
        }
    });
    
    // 切换内容
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    document.getElementById(tab + 'Tab').classList.add('active');
    
    // 初始化对应图表
    setTimeout(() => {
        if (tab === 'intro') initIntroChart();
        if (tab === 'performance') initPerformanceCharts();
        if (tab === 'backtest') initBacktestCharts();
    }, 100);
}

// 收藏按钮
function toggleDetailFav() {
    detailFav = !detailFav;
    const btn = document.getElementById('favBtn');
    btn.textContent = detailFav ? '★ 已收藏' : '☆ 收藏';
    showToast(detailFav ? '已收藏' : '已取消收藏', 'success');
}

// 生成收益曲线数据
function generateReturnData(days = 365, volatility = 0.02, drift = 0.001) {
    const data = [];
    let value = 10000;
    const now = Math.floor(Date.now() / 1000);
    const daySeconds = 86400;
    
    for (let i = days; i >= 0; i--) {
        const time = now - i * daySeconds;
        const change = (Math.random() - 0.5) * volatility + drift;
        value = value * (1 + change);
        data.push({ time, value: value });
    }
    return data;
}

// 生成回撤数据
function generateDrawdownData(returnData) {
    let peak = returnData[0].value;
    return returnData.map(d => {
        if (d.value > peak) peak = d.value;
        const dd = ((d.value - peak) / peak) * 100;
        return { time: d.time, value: dd };
    });
}

// 创建折线图
function createLineChart(containerId, data, color = '#125FFF', isNegative = false) {
    const container = document.getElementById(containerId);
    if (!container || !window.LightweightCharts) return;
    container.innerHTML = '';
    
    const chart = LightweightCharts.createChart(container, {
        width: container.clientWidth,
        height: 250,
        layout: { background: { color: '#fff' }, textColor: '#666' },
        grid: { vertLines: { color: '#f0f0f0' }, horzLines: { color: '#f0f0f0' } },
        rightPriceScale: { borderVisible: false },
        timeScale: { borderVisible: false, timeVisible: true }
    });
    
    const series = chart.addAreaSeries({
        lineColor: color,
        topColor: isNegative ? 'rgba(227,77,89,0.3)' : 'rgba(18,95,255,0.3)',
        bottomColor: isNegative ? 'rgba(227,77,89,0.05)' : 'rgba(18,95,255,0.05)',
        lineWidth: 2
    });
    
    series.setData(data);
    chart.timeScale().fitContent();
    
    window.addEventListener('resize', () => {
        if (container.clientWidth > 0) {
            chart.applyOptions({ width: container.clientWidth });
        }
    });
    
    return chart;
}

// 创建双线图（策略 vs 基准）
function createDualLineChart(containerId, data1, data2) {
    const container = document.getElementById(containerId);
    if (!container || !window.LightweightCharts) return;
    container.innerHTML = '';
    
    const chart = LightweightCharts.createChart(container, {
        width: container.clientWidth,
        height: 250,
        layout: { background: { color: '#fff' }, textColor: '#666' },
        grid: { vertLines: { color: '#f0f0f0' }, horzLines: { color: '#f0f0f0' } },
        rightPriceScale: { borderVisible: false },
        timeScale: { borderVisible: false, timeVisible: true }
    });
    
    const series1 = chart.addLineSeries({ color: '#125FFF', lineWidth: 2 });
    const series2 = chart.addLineSeries({ color: '#999', lineWidth: 1, lineStyle: 2 });
    
    series1.setData(data1);
    series2.setData(data2);
    chart.timeScale().fitContent();
    
    return chart;
}

// 策略说明Tab图表
function initIntroChart() {
    const container = document.getElementById('introReturnChart');
    if (!container || container.dataset.init) return;
    container.dataset.init = 'true';
    
    const data = generateReturnData(180, 0.015, 0.002);
    createLineChart('introReturnChart', data, '#00A870');
}

// 绩效分析Tab图表
function initPerformanceCharts() {
    const container1 = document.getElementById('perfReturnChart');
    if (container1 && !container1.dataset.init) {
        container1.dataset.init = 'true';
        const data = generateReturnData(365, 0.02, 0.002);
        createLineChart('perfReturnChart', data, '#00A870');
    }
    
    const container2 = document.getElementById('perfDrawdownChart');
    if (container2 && !container2.dataset.init) {
        container2.dataset.init = 'true';
        const returnData = generateReturnData(365, 0.02, 0.002);
        const ddData = generateDrawdownData(returnData);
        createLineChart('perfDrawdownChart', ddData, '#E34D59', true);
    }
}

// 回测报告Tab图表
function initBacktestCharts() {
    const container1 = document.getElementById('btEquityChart');
    if (container1 && !container1.dataset.init) {
        container1.dataset.init = 'true';
        const strategyData = generateReturnData(730, 0.02, 0.0015);
        const benchmarkData = generateReturnData(730, 0.025, 0.001);
        createDualLineChart('btEquityChart', strategyData, benchmarkData);
    }
    
    const container2 = document.getElementById('btDrawdownChart');
    if (container2 && !container2.dataset.init) {
        container2.dataset.init = 'true';
        const returnData = generateReturnData(730, 0.02, 0.0015);
        const ddData = generateDrawdownData(returnData);
        createLineChart('btDrawdownChart', ddData, '#E34D59', true);
    }
}

// 策略详情页图表初始化
function initDetailCharts() {
    initIntroChart();
}

// 回测结果页图表
function initResultCharts() {
    const container1 = document.getElementById('resultEquityChart');
    if (container1 && !container1.dataset.init) {
        container1.dataset.init = 'true';
        const strategyData = generateReturnData(365, 0.018, 0.0012);
        const benchmarkData = generateReturnData(365, 0.022, 0.0008);
        createDualLineChart('resultEquityChart', strategyData, benchmarkData);
    }
    
    const container2 = document.getElementById('resultDrawdownChart');
    if (container2 && !container2.dataset.init) {
        container2.dataset.init = 'true';
        const returnData = generateReturnData(365, 0.018, 0.0012);
        const ddData = generateDrawdownData(returnData);
        createLineChart('resultDrawdownChart', ddData, '#E34D59', true);
    }
}

// 实盘监控页图表
function initLiveChart() {
    const container = document.getElementById('liveEquityChart');
    if (!container || container.dataset.init) return;
    container.dataset.init = 'true';
    
    const data = generateReturnData(30, 0.01, 0.003);
    const chart = createLineChart('liveEquityChart', data, '#00A870');
    
    // 模拟实时更新
    if (chart) {
        setInterval(() => {
            const last = data[data.length - 1];
            const newValue = last.value * (1 + (Math.random() - 0.48) * 0.005);
            const newTime = last.time + 60;
            data.push({ time: newTime, value: newValue });
            if (data.length > 500) data.shift();
        }, 5000);
    }
}

// 绩效周期切换
function changePeriod(period) {
    document.querySelectorAll('.period-selector .period-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.textContent.includes(period === '7d' ? '7天' : 
            period === '30d' ? '30天' : 
            period === '90d' ? '90天' : 
            period === '1y' ? '1年' : '全部')) {
            btn.classList.add('active');
        }
    });
    showToast('已切换到' + (period === '7d' ? '近7天' : 
        period === '30d' ? '近30天' : 
        period === '90d' ? '近90天' : 
        period === '1y' ? '近1年' : '全部') + '数据', 'info');
    
    // 重新初始化图表
    const container1 = document.getElementById('perfReturnChart');
    const container2 = document.getElementById('perfDrawdownChart');
    if (container1) container1.dataset.init = '';
    if (container2) container2.dataset.init = '';
    initPerformanceCharts();
}

// 评分选择
let selectedRating = 0;
function setRating(n) {
    selectedRating = n;
    document.querySelectorAll('.star-btn').forEach((btn, i) => {
        btn.textContent = i < n ? '★' : '☆';
        btn.classList.toggle('active', i < n);
    });
}

function toggleFav(i) {
    strategies[i].fav = !strategies[i].fav;
    renderStrategyCards();
    showToast(strategies[i].fav ? '已收藏' : '已取消收藏', 'success');
}

function toggleSub(i) {
    strategies[i].subscribed = !strategies[i].subscribed;
    renderStrategyCards();
    showToast(strategies[i].subscribed ? '订阅成功' : '已取消订阅', 'success');
}

// 回测
function startBacktest() {
    document.getElementById('btProgress').style.display = 'block';
    const fill = document.getElementById('progressFill');
    const pct = document.getElementById('progressPct');
    let p = 0;
    const timer = setInterval(() => {
        p += Math.random() * 10;
        if (p >= 100) {
            p = 100;
            clearInterval(timer);
            setTimeout(() => {
                showToast('回测完成！', 'success');
                showPage('backtestResultPage');
            }, 500);
        }
        fill.style.width = p + '%';
        pct.textContent = Math.floor(p) + '%';
    }, 300);
}

// 实盘
function startLive() {
    if (!document.getElementById('riskCheck')?.checked) {
        showToast('请先确认风险提示', 'warning');
        return;
    }
    showToast('策略启动中...', 'info');
    setTimeout(() => {
        showToast('策略已启动！', 'success');
        showPage('liveMonitorPage');
    }, 1500);
}

// 个人中心切换
function switchProfileTab(tab) {
    const sections = ['basic', 'security', 'exchange', 'notify', 'subscription'];
    sections.forEach(s => {
        document.getElementById(s + 'Section').style.display = 'none';
    });
    document.getElementById(tab + 'Section').style.display = 'block';
    
    document.querySelectorAll('.profile-menu .menu-item').forEach(item => {
        item.classList.remove('active');
    });
    event.target.classList.add('active');
}

// 导航点击
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('nav-item') && e.target.dataset.page) {
        showPage(e.target.dataset.page);
    }
});

// 周期切换
document.querySelectorAll('.period-btns button').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.period-btns button').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        showToast('切换到 ' + btn.textContent + ' 周期', 'info');
    });
});

// ESC关闭模态框
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeModal();
});

// 点击空白关闭下拉菜单
document.addEventListener('click', (e) => {
    if (!e.target.closest('.user-menu')) {
        document.getElementById('userDropdown')?.classList.remove('show');
    }
});

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    showPage('loginPage');
});

// 注册页Tab切换
function switchRegisterType(type) {
    document.querySelectorAll('.auth-tabs .auth-tab').forEach(tab => tab.classList.remove('active'));
    if (type === 'email') {
        document.querySelectorAll('.auth-tabs .auth-tab')[0].classList.add('active');
        document.getElementById('regEmailGroup').style.display = 'block';
        document.getElementById('regPhoneGroup').style.display = 'none';
        document.getElementById('regEmailInput').required = true;
        document.getElementById('regPhoneInput').required = false;
    } else {
        document.querySelectorAll('.auth-tabs .auth-tab')[1].classList.add('active');
        document.getElementById('regEmailGroup').style.display = 'none';
        document.getElementById('regPhoneGroup').style.display = 'block';
        document.getElementById('regEmailInput').required = false;
        document.getElementById('regPhoneInput').required = true;
    }
}

// 忘记密码
let resetStep = 1;
function handleResetPwd(e) {
    e.preventDefault();
    const btn = document.getElementById('resetPwdBtn');
    
    if (resetStep === 1) {
        // 验证账号和验证码
        btn.textContent = '验证中...';
        btn.disabled = true;
        setTimeout(() => {
            btn.textContent = '重置密码';
            btn.disabled = false;
            resetStep = 2;
            document.getElementById('newPwdGroup').style.display = 'block';
            document.getElementById('confirmNewPwdGroup').style.display = 'block';
            showToast('验证成功，请设置新密码', 'success');
        }, 1000);
    } else {
        // 重置密码
        const newPwd = document.getElementById('newPwd').value;
        const confirmPwd = document.getElementById('confirmNewPwd').value;
        if (newPwd.length < 8) {
            showToast('密码至少8位', 'error');
            return;
        }
        if (newPwd !== confirmPwd) {
            showToast('两次密码不一致', 'error');
            return;
        }
        btn.textContent = '重置中...';
        btn.disabled = true;
        setTimeout(() => {
            showToast('密码重置成功！', 'success');
            resetStep = 1;
            setTimeout(() => showPage('loginPage'), 500);
        }, 1000);
    }
}

// 订单Tab切换
function switchOrdersTab(tab) {
    document.querySelectorAll('.orders-tabs span').forEach(t => t.classList.remove('active'));
    if (tab === 'current') {
        document.querySelectorAll('.orders-tabs span')[0].classList.add('active');
        document.getElementById('currentOrdersTable').style.display = 'table';
        document.getElementById('historyOrdersTable').style.display = 'none';
        document.getElementById('orderCount').textContent = '3';
    } else {
        document.querySelectorAll('.orders-tabs span')[1].classList.add('active');
        document.getElementById('currentOrdersTable').style.display = 'none';
        document.getElementById('historyOrdersTable').style.display = 'table';
        document.getElementById('orderCount').textContent = '5';
    }
}

// 指标面板
function showIndicatorPanel() {
    document.getElementById('indicatorPanel').classList.add('show');
    document.getElementById('panelOverlay').classList.add('show');
}

function closeIndicatorPanel() {
    document.getElementById('indicatorPanel').classList.remove('show');
    document.getElementById('panelOverlay').classList.remove('show');
}

function applyIndicators() {
    const checked = document.querySelectorAll('#indicatorPanel input:checked');
    const indicators = Array.from(checked).map(c => c.parentElement.textContent.trim());
    showToast('已应用指标: ' + indicators.join(', '), 'success');
    closeIndicatorPanel();
}

// 画线工具面板
function showDrawingTools() {
    document.getElementById('drawingPanel').classList.add('show');
    document.getElementById('panelOverlay').classList.add('show');
}

function closeDrawingPanel() {
    document.getElementById('drawingPanel').classList.remove('show');
    document.getElementById('panelOverlay').classList.remove('show');
}

function closePanels() {
    closeIndicatorPanel();
    closeDrawingPanel();
}

let selectedTool = null;
function selectDrawingTool(tool) {
    selectedTool = tool;
    document.querySelectorAll('.tool-item').forEach(t => t.classList.remove('active'));
    event.currentTarget.classList.add('active');
    const toolNames = {
        'trendline': '趋势线',
        'horizontal': '水平线',
        'vertical': '垂直线',
        'ray': '射线',
        'channel': '平行通道',
        'fib': '斐波那契',
        'rect': '矩形',
        'circle': '圆形',
        'text': '文字标注',
        'arrow': '箭头'
    };
    showToast('已选择: ' + toolNames[tool] + '，在图表上点击绘制', 'info');
}

function clearAllDrawings() {
    showToast('已清除所有画线', 'success');
}

// ==================== 模拟交易功能 ====================

// 模拟交易模式状态
let isPaperTrading = false;

// 虚拟账户数据
let virtualAccount = {
    balance: 10000.00,
    initialBalance: 10000.00,
    positions: [
        { pair: 'BTC/USDT', side: 'long', amount: 0.1, entryPrice: 43500, symbol: 'BTC' },
        { pair: 'ETH/USDT', side: 'short', amount: 0.5, entryPrice: 3280, symbol: 'ETH' }
    ],
    trades: [],
    totalPnL: 2580.50
};

// 切换交易模式
function toggleTradeMode() {
    isPaperTrading = !isPaperTrading;
    
    // 更新所有模式切换器的显示
    document.querySelectorAll('.trade-mode-switch').forEach(switcher => {
        switcher.classList.toggle('paper', isPaperTrading);
    });
    
    // 更新模拟交易横幅
    updatePaperBanner();
    
    // 显示提示
    if (isPaperTrading) {
        showToast('已切换到模拟交易模式', 'warning');
        showModeChangeConfirm('paper');
    } else {
        showToast('已切换到实盘交易模式', 'success');
        showModeChangeConfirm('live');
    }
    
    // 更新订单面板样式
    updateOrderPanelMode();
}

// 更新模拟交易横幅显示
function updatePaperBanner() {
    const banner = document.getElementById('paperTradingBanner');
    if (banner) {
        banner.style.display = isPaperTrading ? 'flex' : 'none';
        if (isPaperTrading) {
            const balanceEl = document.getElementById('bannerBalance');
            if (balanceEl) {
                balanceEl.textContent = virtualAccount.balance.toLocaleString('en-US', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                }) + ' USDT';
            }
        }
    }
}

// 更新订单面板模式
function updateOrderPanelMode() {
    const orderPanel = document.querySelector('.order-panel');
    const ordersSection = document.querySelector('.orders-section');
    
    if (orderPanel) {
        orderPanel.classList.toggle('paper-mode', isPaperTrading);
    }
    if (ordersSection) {
        ordersSection.classList.toggle('paper-mode', isPaperTrading);
    }
}

// 显示模式切换确认
function showModeChangeConfirm(mode) {
    // 可以在这里添加更详细的模式说明弹窗
    console.log('Mode changed to:', mode);
}

// 模拟下单
function submitPaperOrder(side, price, amount, pair = 'BTC/USDT') {
    if (!isPaperTrading) {
        showToast('请先切换到模拟交易模式', 'warning');
        return false;
    }
    
    const total = price * amount;
    
    // 检查余额
    if (side === 'buy' && total > virtualAccount.balance) {
        showToast('虚拟账户余额不足', 'error');
        return false;
    }
    
    // 模拟订单撮合延迟
    showToast('模拟订单提交中...', 'info');
    
    setTimeout(() => {
        // 模拟订单成交
        const trade = {
            time: new Date().toISOString(),
            pair: pair,
            side: side,
            price: price,
            amount: amount,
            total: total,
            type: 'limit',
            status: 'filled'
        };
        
        virtualAccount.trades.unshift(trade);
        
        // 更新余额
        if (side === 'buy') {
            virtualAccount.balance -= total;
        } else {
            virtualAccount.balance += total;
        }
        
        showToast(`模拟订单成交: ${side === 'buy' ? '买入' : '卖出'} ${amount} ${pair.split('/')[0]} @ ${price}`, 'success');
        
        // 更新显示
        updatePaperBanner();
    }, 500 + Math.random() * 1000);
    
    return true;
}

// 重置虚拟账户
function showResetModal() {
    document.getElementById('resetModal').classList.add('show');
}

function closeResetModal() {
    document.getElementById('resetModal').classList.remove('show');
}

function confirmResetAccount() {
    virtualAccount.balance = virtualAccount.initialBalance;
    virtualAccount.positions = [];
    virtualAccount.trades = [];
    virtualAccount.totalPnL = 0;
    
    closeResetModal();
    showToast('虚拟账户已重置，初始资金: 10,000 USDT', 'success');
    
    // 刷新页面数据
    if (document.getElementById('virtualAccountPage').classList.contains('active')) {
        updateVirtualAccountDisplay();
    }
    updatePaperBanner();
}

// 调整资金弹窗
function showAdjustModal() {
    document.getElementById('adjustModal').classList.add('show');
}

function closeAdjustModal() {
    document.getElementById('adjustModal').classList.remove('show');
}

function setAdjustAmount(amount) {
    document.getElementById('adjustAmount').value = amount;
}

function confirmAdjustBalance() {
    const amount = parseFloat(document.getElementById('adjustAmount').value);
    const isAdd = document.querySelector('input[name="adjustType"]:checked').value === 'add';
    
    if (isNaN(amount) || amount <= 0) {
        showToast('请输入有效金额', 'error');
        return;
    }
    
    if (isAdd) {
        virtualAccount.balance += amount;
        showToast(`已增加 ${amount.toLocaleString()} USDT 虚拟资金`, 'success');
    } else {
        if (amount > virtualAccount.balance) {
            showToast('减少金额不能超过当前余额', 'error');
            return;
        }
        virtualAccount.balance -= amount;
        showToast(`已减少 ${amount.toLocaleString()} USDT 虚拟资金`, 'success');
    }
    
    closeAdjustModal();
    updatePaperBanner();
    updateVirtualAccountDisplay();
}

// 更新虚拟账户显示
function updateVirtualAccountDisplay() {
    const totalAssetsEl = document.getElementById('totalAssets');
    if (totalAssetsEl) {
        // 计算总资产 = 余额 + 持仓价值
        const positionValue = virtualAccount.positions.reduce((sum, pos) => {
            const currentPrice = pos.symbol === 'BTC' ? 45230 : 3200;
            return sum + (pos.amount * currentPrice);
        }, 0);
        const total = virtualAccount.balance + positionValue;
        totalAssetsEl.textContent = total.toLocaleString('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }) + ' USDT';
    }
}

// 平掉模拟持仓
function closePaperPosition(symbol) {
    const posIndex = virtualAccount.positions.findIndex(p => p.symbol === symbol);
    if (posIndex === -1) {
        showToast('未找到持仓', 'error');
        return;
    }
    
    const pos = virtualAccount.positions[posIndex];
    const currentPrice = symbol === 'BTC' ? 45230 : 3200;
    const pnl = pos.side === 'long' 
        ? (currentPrice - pos.entryPrice) * pos.amount
        : (pos.entryPrice - currentPrice) * pos.amount;
    
    // 更新余额
    virtualAccount.balance += (pos.amount * currentPrice) + pnl;
    virtualAccount.totalPnL += pnl;
    
    // 移除持仓
    virtualAccount.positions.splice(posIndex, 1);
    
    // 添加交易记录
    virtualAccount.trades.unshift({
        time: new Date().toISOString(),
        pair: pos.pair,
        side: pos.side === 'long' ? 'sell' : 'buy',
        price: currentPrice,
        amount: pos.amount,
        pnl: pnl,
        type: 'market',
        status: 'filled'
    });
    
    showToast(`已平仓 ${symbol}: ${pnl >= 0 ? '盈利' : '亏损'} ${Math.abs(pnl).toFixed(2)} USDT`, pnl >= 0 ? 'success' : 'warning');
    
    // 刷新持仓表格
    updatePaperPositionsTable();
    updatePaperBanner();
}

// 更新持仓表格
function updatePaperPositionsTable() {
    const tbody = document.getElementById('paperPositions');
    if (!tbody) return;
    
    if (virtualAccount.positions.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;color:var(--text2);">暂无持仓</td></tr>';
        return;
    }
    
    tbody.innerHTML = virtualAccount.positions.map(pos => {
        const currentPrice = pos.symbol === 'BTC' ? 45230 : 3200;
        const pnl = pos.side === 'long' 
            ? (currentPrice - pos.entryPrice) * pos.amount
            : (pos.entryPrice - currentPrice) * pos.amount;
        const pnlPct = (pnl / (pos.entryPrice * pos.amount) * 100).toFixed(2);
        const isPositive = pnl >= 0;
        
        return `
            <tr>
                <td><span class="pair-badge">${pos.pair}</span></td>
                <td><span class="side-badge ${pos.side}">${pos.side === 'long' ? '多' : '空'}</span></td>
                <td>${pos.amount} ${pos.symbol}</td>
                <td>${pos.entryPrice.toLocaleString()}</td>
                <td>${currentPrice.toLocaleString()}</td>
                <td class="${isPositive ? 'positive' : 'negative'}">${isPositive ? '+' : ''}${pnl.toFixed(2)} USDT</td>
                <td class="${isPositive ? 'positive' : 'negative'}">${isPositive ? '+' : ''}${pnlPct}%</td>
                <td><button class="btn-small danger" onclick="closePaperPosition('${pos.symbol}')">平仓</button></td>
            </tr>
        `;
    }).join('');
}

// 初始化模拟账户资金曲线图表
function initPaperEquityChart() {
    const container = document.getElementById('paperEquityChart');
    if (!container || container.dataset.init) return;
    container.dataset.init = 'true';
    
    const data = generateReturnData(30, 0.015, 0.002);
    createLineChart('paperEquityChart', data, '#FF9800');
}

// 初始化模拟监控页实时图表
function initPaperLiveChart() {
    const container = document.getElementById('paperLiveEquityChart');
    if (!container || container.dataset.init) return;
    container.dataset.init = 'true';
    
    const data = generateReturnData(7, 0.012, 0.003);
    createLineChart('paperLiveEquityChart', data, '#FF9800');
}

// 启动模拟策略
function startPaperStrategy() {
    if (!isPaperTrading) {
        showToast('请先切换到模拟交易模式', 'warning');
        return;
    }
    
    showToast('模拟策略启动中...', 'info');
    setTimeout(() => {
        showToast('模拟策略已启动！', 'success');
        showPage('paperMonitorPage');
    }, 1500);
}

// 模拟订单撮合逻辑（简化版）
function simulateOrderMatch(order) {
    // 模拟撮合延迟
    const delay = 100 + Math.random() * 500;
    
    return new Promise((resolve) => {
        setTimeout(() => {
            // 模拟成交
            const fillPrice = order.type === 'market' 
                ? order.price * (1 + (Math.random() - 0.5) * 0.001) // 市价单有滑点
                : order.price;
            
            resolve({
                ...order,
                fillPrice: fillPrice,
                fillTime: new Date().toISOString(),
                status: 'filled'
            });
        }, delay);
    });
}

// 获取模拟交易统计
function getPaperTradingStats() {
    const trades = virtualAccount.trades;
    const winTrades = trades.filter(t => t.pnl > 0);
    const loseTrades = trades.filter(t => t.pnl < 0);
    
    return {
        totalTrades: trades.length,
        winRate: trades.length > 0 ? (winTrades.length / trades.length * 100).toFixed(1) : 0,
        avgWin: winTrades.length > 0 ? (winTrades.reduce((s, t) => s + t.pnl, 0) / winTrades.length).toFixed(2) : 0,
        avgLoss: loseTrades.length > 0 ? (loseTrades.reduce((s, t) => s + t.pnl, 0) / loseTrades.length).toFixed(2) : 0,
        totalPnL: virtualAccount.totalPnL
    };
}

// 导出模拟交易报告
function exportPaperReport() {
    const stats = getPaperTradingStats();
    showToast('模拟交易报告导出中...', 'info');
    setTimeout(() => {
        showToast('报告已导出！', 'success');
    }, 1500);
}

// 初始化时设置模式切换器状态
document.addEventListener('DOMContentLoaded', () => {
    // 初始化所有模式切换器
    document.querySelectorAll('.trade-mode-switch').forEach(switcher => {
        switcher.classList.toggle('paper', isPaperTrading);
    });
});

// 重写下单函数以支持模拟交易
const originalSubmitOrder = submitOrder;
function submitOrder() {
    const amt = parseFloat(document.getElementById('orderAmt')?.value);
    if (!amt || amt <= 0) {
        showToast('请输入数量', 'error');
        return;
    }
    
    if (isPaperTrading) {
        // 模拟交易模式
        const price = 45230.50;
        submitPaperOrder(orderSide, price, amt);
    } else {
        // 实盘交易模式
        const btn = document.getElementById('orderBtn');
        btn.textContent = '提交中...';
        btn.disabled = true;
        setTimeout(() => {
            btn.textContent = orderSide === 'buy' ? '买入 BTC' : '卖出 BTC';
            btn.disabled = false;
            showToast('订单提交成功！', 'success');
        }, 1000);
    }
}

// ============================================
// 合约交易功能 (F002B)
// ============================================

let currentLeverage = 10;
let currentMarginMode = 'isolated';
let contractSide = 'long';

// 设置杠杆
function setLeverage(leverage) {
    currentLeverage = leverage;
    document.querySelectorAll('.leverage-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    document.getElementById('customLeverage').value = leverage;
    calcContractOrder();
    showToast(`杠杆已设置为 ${leverage}x`, 'info');
}

// 自定义杠杆更新
function updateLeverage() {
    const value = parseInt(document.getElementById('customLeverage').value);
    if (value < 1) {
        document.getElementById('customLeverage').value = 1;
        currentLeverage = 1;
    } else if (value > 20) {
        document.getElementById('customLeverage').value = 20;
        currentLeverage = 20;
        showToast('P0版本最高支持20x杠杆', 'warning');
    } else {
        currentLeverage = value;
    }
    // 更新按钮状态
    document.querySelectorAll('.leverage-btn').forEach(btn => {
        btn.classList.remove('active');
        if (parseInt(btn.textContent) === currentLeverage) {
            btn.classList.add('active');
        }
    });
    calcContractOrder();
}

// 设置保证金模式
function setMarginMode(mode) {
    currentMarginMode = mode;
    document.querySelectorAll('.margin-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    if (!event.target.classList.contains('disabled')) {
        event.target.classList.add('active');
    }
}

// 切换合约方向
function switchContractSide(side) {
    contractSide = side;
    document.querySelectorAll('.direction-tab').forEach(t => {
        t.classList.remove('active');
    });
    document.querySelector(`.direction-tab.${side}`).classList.add('active');
    
    const btn = document.getElementById('contractOrderBtn');
    btn.className = `order-submit contract-submit ${side}`;
    btn.textContent = side === 'long' ? '🟢 开多 BTC' : '🔴 开空 BTC';
}

// 计算合约订单信息
function calcContractOrder() {
    const price = parseFloat(document.getElementById('contractPrice')?.value) || 45230.50;
    const amount = parseFloat(document.getElementById('contractAmount')?.value) || 0;
    const leverage = currentLeverage;
    
    if (amount > 0) {
        const orderValue = price * amount;
        const requiredMargin = orderValue / leverage;
        
        // 计算强平价格 (简化计算)
        const maintenanceRate = 0.004; // 维持保证金率
        let liqPrice;
        if (contractSide === 'long') {
            liqPrice = price * (1 - (1/leverage) + maintenanceRate);
        } else {
            liqPrice = price * (1 + (1/leverage) - maintenanceRate);
        }
        
        document.getElementById('requiredMargin').textContent = requiredMargin.toFixed(2) + ' USDT';
        document.getElementById('estLiquidation').textContent = liqPrice.toFixed(2) + ' USDT';
    } else {
        document.getElementById('requiredMargin').textContent = '0.00 USDT';
        document.getElementById('estLiquidation').textContent = '-- USDT';
    }
}

// 设置合约数量百分比
function setContractAmt(pct) {
    const availableMargin = 5000;
    const price = parseFloat(document.getElementById('contractPrice')?.value) || 45230.50;
    const leverage = currentLeverage;
    const maxValue = availableMargin * leverage;
    const amt = (maxValue * pct / 100 / price).toFixed(6);
    document.getElementById('contractAmount').value = amt;
    calcContractOrder();
}

// 切换止盈止损
function toggleTpSl() {
    const inputs = document.getElementById('tpSlInputs');
    const checkbox = document.getElementById('tpSlCheckbox');
    const arrow = document.getElementById('tpSlArrow');
    
    if (inputs.style.display === 'none') {
        inputs.style.display = 'block';
        checkbox.checked = true;
        arrow.textContent = '▲';
    } else {
        inputs.style.display = 'none';
        checkbox.checked = false;
        arrow.textContent = '▼';
    }
}

// 提交合约订单
function submitContractOrder() {
    const amount = parseFloat(document.getElementById('contractAmount')?.value);
    if (!amount || amount <= 0) {
        showToast('请输入数量', 'error');
        return;
    }
    
    // 显示确认弹窗
    showContractConfirmModal();
}

// 显示合约确认弹窗
function showContractConfirmModal() {
    const price = document.getElementById('contractPrice').value;
    const amount = document.getElementById('contractAmount').value;
    const leverage = currentLeverage;
    const value = (price * amount).toFixed(2);
    const margin = (value / leverage).toFixed(2);
    
    // 计算强平价格
    let liqPrice;
    if (contractSide === 'long') {
        liqPrice = (price * (1 - (1/leverage) + 0.004)).toFixed(2);
    } else {
        liqPrice = (price * (1 + (1/leverage) - 0.004)).toFixed(2);
    }
    const liqDistance = ((liqPrice - price) / price * 100).toFixed(2);
    
    document.getElementById('confirmContractType').textContent = 'BTC/USDT 永续合约';
    document.getElementById('confirmDirection').textContent = contractSide === 'long' ? '🟢 开多' : '🔴 开空';
    document.getElementById('confirmDirection').className = contractSide === 'long' ? 'direction-long' : 'direction-short';
    document.getElementById('confirmLeverage').textContent = leverage + 'x';
    document.getElementById('confirmMarginMode').textContent = currentMarginMode === 'isolated' ? '逐仓' : '全仓';
    document.getElementById('confirmPrice').textContent = parseFloat(price).toLocaleString() + ' USDT';
    document.getElementById('confirmAmount').textContent = amount + ' BTC';
    document.getElementById('confirmValue').textContent = parseFloat(value).toLocaleString() + ' USDT';
    document.getElementById('confirmMargin').textContent = parseFloat(margin).toLocaleString() + ' USDT';
    document.getElementById('confirmLiqPrice').innerHTML = parseFloat(liqPrice).toLocaleString() + ' USDT <small>(🔴 距当前价 ' + liqDistance + '%)</small>';
    
    document.getElementById('riskConfirmCheckbox').checked = false;
    document.getElementById('confirmContractBtn').disabled = true;
    document.getElementById('contractConfirmModal').classList.add('show');
}

function closeContractConfirmModal() {
    document.getElementById('contractConfirmModal').classList.remove('show');
}

function updateConfirmBtn() {
    const checked = document.getElementById('riskConfirmCheckbox').checked;
    document.getElementById('confirmContractBtn').disabled = !checked;
}

function confirmContractOrder() {
    closeContractConfirmModal();
    showToast('合约订单提交中...', 'info');
    setTimeout(() => {
        showToast('合约订单提交成功！', 'success');
        document.getElementById('contractAmount').value = '';
        calcContractOrder();
    }, 1000);
}

// 切换合约持仓/委托标签
function switchContractTab(tab) {
    document.querySelectorAll('.contract-orders-section .orders-tabs span').forEach(t => {
        t.classList.remove('active');
    });
    event.target.classList.add('active');
    
    document.getElementById('contractPositionsTable').style.display = tab === 'positions' ? 'table' : 'none';
    document.getElementById('contractOrdersTable').style.display = tab === 'orders' ? 'table' : 'none';
}

// 一键平仓弹窗
function showCloseAllModal() {
    document.getElementById('closeAllModal').classList.add('show');
}

function closeCloseAllModal() {
    document.getElementById('closeAllModal').classList.remove('show');
}

function confirmCloseAll() {
    closeCloseAllModal();
    showToast('正在平仓所有持仓...', 'info');
    setTimeout(() => {
        showToast('所有持仓已平仓', 'success');
    }, 1500);
}

// 显示止盈止损设置弹窗
function showTpSlModal(symbol) {
    showToast('止盈止损设置功能开发中', 'info');
}

// 显示平仓确认弹窗
function showClosePositionModal(symbol) {
    showModal('确认平仓', `确定要平仓 ${symbol} 持仓吗？`);
}

// 合约交易对选择器
function showContractPairSelector() {
    showToast('合约交易对选择器开发中', 'info');
}

// ============================================
// 策略模拟监控功能 (F007B)
// ============================================

// 显示策略模拟详情
function showSimDetail(strategyId) {
    showPage('paperMonitorPage');
}

// 暂停模拟策略
function pauseSimStrategy(strategyId) {
    showToast(`策略 ${strategyId} 已暂停`, 'warning');
    // 更新卡片状态
    setTimeout(() => {
        location.reload();
    }, 500);
}

// 恢复模拟策略
function resumeSimStrategy(strategyId) {
    showToast(`策略 ${strategyId} 已恢复运行`, 'success');
}

// 停止模拟策略
function stopSimStrategy(strategyId) {
    showModal('停止策略', `确定要停止策略 ${strategyId} 的模拟运行吗？此操作不可撤销。`);
}

// 切换我的策略页面的实盘/模拟模式
let currentStrategyMode = 'live';
function switchStrategyMode(mode) {
    currentStrategyMode = mode;
    
    // 更新标签激活状态
    document.querySelectorAll('.strategy-mode-tabs .mode-tab').forEach(tab => {
        tab.classList.remove('active');
        // 根据按钮文本内容判断是哪个模式
        if ((mode === 'live' && tab.textContent.includes('实盘')) || 
            (mode === 'sim' && tab.textContent.includes('模拟'))) {
            tab.classList.add('active');
        }
    });
    
    // 切换列表显示
    const liveList = document.getElementById('liveStrategyList');
    const simList = document.getElementById('simStrategyList');
    
    if (mode === 'live') {
        liveList.style.display = 'block';
        simList.style.display = 'none';
    } else {
        liveList.style.display = 'none';
        simList.style.display = 'block';
    }
}

// 启动策略模拟弹窗
function showStartSimModal() {
    document.getElementById('startSimModal').classList.add('show');
}

function closeStartSimModal() {
    document.getElementById('startSimModal').classList.remove('show');
}

function confirmStartSim() {
    const strategy = document.getElementById('simStrategySelect').value;
    const account = document.getElementById('simAccountSelect').value;
    const capital = document.getElementById('simCapitalInput').value;
    
    closeStartSimModal();
    showToast(`正在启动策略模拟...`, 'info');
    
    setTimeout(() => {
        showToast(`策略模拟已启动！投入资金: ${capital} USDT`, 'success');
        showPage('strategySimPage');
    }, 1500);
}

// 模拟vs回测对比弹窗
function showCompareModal(strategyId) {
    document.getElementById('compareModal').classList.add('show');
}

function closeCompareModal() {
    document.getElementById('compareModal').classList.remove('show');
}

// 策略异常告警弹窗
function showSimAlertModal() {
    document.getElementById('simAlertModal').classList.add('show');
}

function closeSimAlertModal() {
    document.getElementById('simAlertModal').classList.remove('show');
}

function stopAlertStrategy() {
    closeSimAlertModal();
    showToast('策略已停止', 'warning');
}

function resumeAlertStrategy() {
    closeSimAlertModal();
    showToast('请先调整策略参数', 'info');
}

// 初始化合约图表
function initContractChart() {
    const container = document.getElementById('contractChartContainer');
    if (!container || !window.LightweightCharts) return;
    
    const chart = LightweightCharts.createChart(container, {
        width: container.clientWidth,
        height: 450,
        layout: { background: { color: '#0d1117' }, textColor: '#d1d5db' },
        grid: { vertLines: { color: '#1f2937' }, horzLines: { color: '#1f2937' } },
        timeScale: { borderColor: '#374151', timeVisible: true }
    });
    
    const candleSeries = chart.addCandlestickSeries({
        upColor: '#00A870',
        downColor: '#E34D59',
        borderUpColor: '#00A870',
        borderDownColor: '#E34D59',
        wickUpColor: '#00A870',
        wickDownColor: '#E34D59'
    });
    
    // 生成模拟数据
    const data = [];
    let time = new Date();
    time.setHours(time.getHours() - 100);
    let price = 45000;
    
    for (let i = 0; i < 100; i++) {
        const open = price;
        const close = open + (Math.random() - 0.48) * 500;
        const high = Math.max(open, close) + Math.random() * 200;
        const low = Math.min(open, close) - Math.random() * 200;
        
        data.push({
            time: Math.floor(time.getTime() / 1000),
            open, high, low, close
        });
        
        price = close;
        time.setHours(time.getHours() + 1);
    }
    
    candleSeries.setData(data);
}

// 页面加载时初始化合约图表
document.addEventListener('DOMContentLoaded', () => {
    // 延迟初始化，避免页面加载时阻塞
    setTimeout(() => {
        if (document.getElementById('contractChartContainer')) {
            initContractChart();
        }
    }, 100);
});

// ===================== 新增页面功能 =====================

// 自选管理功能 (US-005)
function switchWatchlistGroup(tab) {
    document.querySelectorAll('.watchlist-tab').forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
    showToast('已切换到 ' + tab.textContent, 'info');
}

function showAddWatchlistModal() {
    document.getElementById('addWatchlistModal').classList.add('show');
}

function closeAddWatchlistModal() {
    document.getElementById('addWatchlistModal').classList.remove('show');
}

function searchPairs(query) {
    // 模拟搜索功能
    console.log('搜索交易对:', query);
}

function addToWatchlist(pair) {
    showToast(`已添加 ${pair} 到自选`, 'success');
    closeAddWatchlistModal();
}

function removeFromWatchlist(pair) {
    if (confirm(`确定要从自选中移除 ${pair} 吗？`)) {
        showToast(`已移除 ${pair}`, 'info');
    }
}

// 价格预警功能 (US-007)
function showCreateAlertModal() {
    document.getElementById('createAlertModal').classList.add('show');
}

function closeCreateAlertModal() {
    document.getElementById('createAlertModal').classList.remove('show');
}

function confirmCreateAlert() {
    const pair = document.getElementById('alertPair')?.value || 'BTC/USDT';
    const condition = document.getElementById('alertCondition')?.value || '价格高于';
    const price = document.getElementById('alertPrice')?.value || '100000';
    
    showToast(`预警已创建: ${pair} ${condition} $${price}`, 'success');
    closeCreateAlertModal();
}

function editAlert(id) {
    showToast('编辑预警 #' + id, 'info');
    showCreateAlertModal();
}

function deleteAlert(id) {
    if (confirm('确定要删除这条预警吗？')) {
        showToast('预警已删除', 'success');
    }
}

function toggleNotifyChannel(element) {
    element.classList.toggle('active');
    const channelName = element.parentElement.querySelector('.channel-name').textContent;
    const isActive = element.classList.contains('active');
    showToast(`${channelName} 通知已${isActive ? '开启' : '关闭'}`, 'info');
}

// 多交易所对比功能 (US-008)
function refreshCompareData() {
    showToast('正在刷新价格数据...', 'info');
    setTimeout(() => {
        showToast('价格数据已更新', 'success');
    }, 1000);
}

function changeComparePair(select) {
    const pair = select.value;
    showToast(`已切换到 ${pair} 对比`, 'info');
}

// 策略模板功能 (US-032)
function previewTemplate(templateId) {
    const templateNames = {
        'ma-cross': '均线交叉策略',
        'grid': '网格交易策略',
        'macd': 'MACD趋势策略',
        'dca': '定投策略',
        'bollinger': '布林带突破策略',
        'arbitrage': '套利策略',
        'rsi': 'RSI超买超卖策略',
        'turtle': '海龟交易策略'
    };
    
    showModal(
        templateNames[templateId] || '策略预览',
        `策略ID: ${templateId}\n\n该策略包含完整的买入/卖出逻辑、风控规则和参数配置。\n\n点击"使用模板"可以快速创建基于此模板的个人策略。`
    );
}

function useTemplate(templateId) {
    const templateNames = {
        'ma-cross': '均线交叉策略',
        'grid': '网格交易策略',
        'macd': 'MACD趋势策略',
        'dca': '定投策略',
        'bollinger': '布林带突破策略',
        'arbitrage': '套利策略',
        'rsi': 'RSI超买超卖策略',
        'turtle': '海龟交易策略'
    };
    
    showToast(`正在基于"${templateNames[templateId]}"创建策略...`, 'info');
    setTimeout(() => {
        showPage('myStrategyPage');
        showToast('策略已创建，请配置参数', 'success');
    }, 500);
}

function filterTemplates(category) {
    document.querySelectorAll('.category-tag').forEach(tag => tag.classList.remove('active'));
    event.target.classList.add('active');
    showToast(`筛选: ${category === 'all' ? '全部' : category}`, 'info');
}

// SDK文档功能 (US-033)
function switchSdkDoc(docId, element) {
    document.querySelectorAll('.sdk-nav-item').forEach(item => item.classList.remove('active'));
    element.classList.add('active');
    
    // 这里可以根据docId加载不同的文档内容
    const docTitles = {
        'quick-start': '快速开始',
        'api-reference': 'API参考',
        'market-data': '行情数据',
        'order-api': '订单接口',
        'account-api': '账户接口',
        'strategy-sdk': '策略SDK',
        'backtest': '回测引擎',
        'examples': '示例代码'
    };
    
    showToast(`已切换到: ${docTitles[docId] || docId}`, 'info');
}

function copyCode(button) {
    const codeBlock = button.parentElement.querySelector('pre');
    const code = codeBlock.textContent;
    
    navigator.clipboard.writeText(code).then(() => {
        const originalText = button.textContent;
        button.textContent = '已复制!';
        setTimeout(() => {
            button.textContent = originalText;
        }, 2000);
    }).catch(() => {
        showToast('复制失败，请手动复制', 'error');
    });
}

// 资产详情功能 (US-020)
function filterTransactions(type) {
    document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    showToast(`筛选: ${type === 'all' ? '全部' : type === 'buy' ? '买入' : '卖出'}`, 'info');
}

// 手续费统计功能 (US-022)
function exportFeeReport() {
    showToast('正在导出手续费报表...', 'info');
    setTimeout(() => {
        showToast('报表已导出', 'success');
    }, 1000);
}

// 导航功能扩展
function navigateToPage(pageName) {
    showPage(pageName);
}

// 扩展showPage函数以支持新页面
const originalShowPage = showPage;
showPage = function(pageId) {
    // 支持所有新页面
    const newPages = [
        'marketOverviewPage', 
        'exchangeComparePage', 
        'watchlistPage', 
        'priceAlertPage',
        'assetDetailPage',
        'feeStatPage',
        'strategyTemplatePage',
        'sdkDocPage',
        'notificationPage',
        'communityPage'
    ];
    
    if (newPages.includes(pageId)) {
        document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
        const targetPage = document.getElementById(pageId);
        if (targetPage) {
            targetPage.classList.add('active');
            // 更新导航状态
            document.querySelectorAll('.nav-item').forEach(item => {
                item.classList.remove('active');
                if (item.dataset.page === pageId) {
                    item.classList.add('active');
                }
            });
        }
        return;
    }
    
    // 调用原有的showPage函数
    if (typeof originalShowPage === 'function') {
        originalShowPage(pageId);
    } else {
        // 基础实现
        document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
        const targetPage = document.getElementById(pageId);
        if (targetPage) {
            targetPage.classList.add('active');
        }
    }
};

// ===================== 技术指标功能 =====================
function toggleIndicatorDropdown(type) {
    const dropdownId = type === 'contract' ? 'contractIndicatorDropdown' : 'indicatorDropdown';
    const dropdown = document.getElementById(dropdownId);
    if (dropdown) {
        dropdown.classList.toggle('show');
    }
}

function toggleIndicator(indicator) {
    updateIndicatorCount();
    showToast(`${indicator} 指标已切换`, 'info');
}

function updateIndicatorCount() {
    const dropdown = document.getElementById('indicatorDropdown');
    if (dropdown) {
        const checked = dropdown.querySelectorAll('input[type="checkbox"]:checked').length;
        const countEl = document.getElementById('indicatorCount');
        if (countEl) {
            countEl.textContent = checked;
        }
    }
}

function removeIndicator(indicator) {
    const activeIndicators = document.getElementById('activeIndicators');
    if (activeIndicators) {
        const indicatorEl = activeIndicators.querySelector(`[data-indicator="${indicator}"]`);
        if (indicatorEl) {
            indicatorEl.remove();
        }
    }
    showToast(`已移除 ${indicator} 指标`, 'info');
}

function resetIndicators() {
    document.querySelectorAll('.indicator-dropdown input[type="checkbox"]').forEach(cb => {
        cb.checked = false;
    });
    updateIndicatorCount();
    showToast('已重置所有指标', 'info');
}

function applyIndicators() {
    const dropdown = document.getElementById('indicatorDropdown');
    if (dropdown) {
        dropdown.classList.remove('show');
    }
    const contractDropdown = document.getElementById('contractIndicatorDropdown');
    if (contractDropdown) {
        contractDropdown.classList.remove('show');
    }
    showToast('指标设置已应用', 'success');
}

function switchChartType(type) {
    document.querySelectorAll('.contract-chart-tools .tool-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    showToast(`已切换到${type === 'candle' ? 'K线' : type === 'line' ? '分时' : '深度'}图`, 'info');
}

// ===================== 消息通知功能 =====================
function switchNotifTab(type, element) {
    document.querySelectorAll('.notif-tab').forEach(tab => tab.classList.remove('active'));
    element.classList.add('active');
    showToast(`筛选: ${type === 'all' ? '全部' : type}`, 'info');
}

function markAllRead() {
    document.querySelectorAll('.notification-item.unread').forEach(item => {
        item.classList.remove('unread');
    });
    document.querySelectorAll('.notif-status.unread').forEach(status => {
        status.classList.remove('unread');
        status.classList.add('read');
        status.textContent = '已读';
    });
    showToast('已全部标记为已读', 'success');
}

function clearNotifications() {
    if (confirm('确定要清空所有消息吗？')) {
        showToast('消息已清空', 'success');
    }
}

function viewNotification(id) {
    showToast(`查看消息 #${id}`, 'info');
}

// ===================== 社区功能 =====================
function switchContentTab(type, element) {
    document.querySelectorAll('.content-tab').forEach(tab => tab.classList.remove('active'));
    element.classList.add('active');
}

function publishPost() {
    const content = document.getElementById('postContent');
    if (content && content.value.trim()) {
        showToast('动态发布成功！', 'success');
        content.value = '';
    } else {
        showToast('请输入内容后再发布', 'error');
    }
}

function addPostImage() {
    showToast('选择图片功能', 'info');
}

function addPostChart() {
    showToast('添加K线截图', 'info');
}

function addPostPoll() {
    showToast('创建投票', 'info');
}

function addPostTopic() {
    showToast('添加话题标签', 'info');
}

function likePost(id) {
    showToast('点赞成功！', 'success');
}

function showComments(id) {
    showToast(`查看评论 #${id}`, 'info');
}

function sharePost(id) {
    showToast('分享链接已复制', 'success');
}

function collectPost(id) {
    showToast('已收藏到我的收藏', 'success');
}

function toggleFollow(element) {
    if (element.classList.contains('following')) {
        element.classList.remove('following');
        element.textContent = '+ 关注';
        showToast('已取消关注', 'info');
    } else {
        element.classList.add('following');
        element.textContent = '已关注';
        showToast('关注成功', 'success');
    }
}

function votePoll(pollId, option) {
    showToast(`已投票: ${option}`, 'success');
}

function searchTopic(topic) {
    showToast(`搜索话题: #${topic}`, 'info');
}

function loadMorePosts() {
    showToast('正在加载更多...', 'info');
}

// 点击外部关闭下拉菜单
document.addEventListener('click', function(e) {
    if (!e.target.closest('.indicator-selector')) {
        document.querySelectorAll('.indicator-dropdown').forEach(dropdown => {
            dropdown.classList.remove('show');
        });
    }
});
