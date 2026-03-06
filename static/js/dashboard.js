// ─────────────────────────────────────────────────────────────────
//  dashboard.js — market-terminal
//  Connects the UI to Flask-SocketIO backend
// ─────────────────────────────────────────────────────────────────

let symbols     = window.SYMBOLS || [];
let activeSymbol  = symbols[0] || null;
let currentSide   = 'buy';
let userKey       = sessionStorage.getItem('api_key');
let cashBalance   = 10000;

// Per-symbol candle history for QFChart
const candleHistory = {}; // { sym: [{time, open, high, low, close, volume}] }
let chart = null;


//
// REDIRECTION TO LOGIN IF NO API KEY
//
if (!userKey) {
  console.warn('No API key found, redirecting to login');
  window.location.href = '/auth';
}
//
// ─────────────────────────────────────────────────────────────────
//  SOCKET
// ─────────────────────────────────────────────────────────────────
const socket = io();

socket.on('connect', () => {
  console.log('[WS] connected:', socket.id);
  updateSessionBadge(true);
});

socket.on('disconnect', () => {
  updateSessionBadge(false);
});

// Trade happened → update chart + recent trades
socket.on('made_trade', (data) => {
  const { symbol, price, quantity } = data;
  addTradeToChart(symbol, price, quantity);
  updateSymbolPrice(symbol, price);
});

// Personal order confirmation
socket.on('trade_result', (data) => {
  console.log('[trade_result]', data);
  // TODO: update portfolio from response
});

socket.on('game_start', (data) => {
  const { symbols: socket_symbols} = data;
  socket_symbols.forEach(s => updateSymbolPrice(s.name, s.price));
  symbols = socket_symbols.map(s => s.name);
  activeSymbol = symbols[0];
  renderSymbolTabs(socket_symbols);
});
// Game State Updates
socket.on('time_update', (data) => {
  const { time_left } = data;
  const m = Math.floor(time_left / 60).toString().padStart(2, '0');
  const s = (time_left % 60).toString().padStart(2, '0');
  document.getElementById('timer').textContent = `${m}:${s}`;
});

// ─────────────────────────────────────────────────────────────────
//  CHART (QFChart)
// ─────────────────────────────────────────────────────────────────
let priceLineIndicator = null;

function initChart(sym) {
  const el = document.getElementById('qf-mount');
  if (!el || typeof QFChart === 'undefined') return;
  if (chart) { try { chart.destroy(); } catch(e) {} }
  priceLineIndicator = null;
  el.innerHTML = '';
  const dark = document.documentElement.getAttribute('data-theme') === 'dark';
  chart = new QFChart.QFChart(el, {
    height: '400px',
    backgroundColor: dark ? '#1a1a18' : '#ffffff',
    upColor:         dark ? '#2ecc71' : '#1a7a4a',
    downColor:       dark ? '#e74c3c' : '#c0392b',
    fontColor:       dark ? '#5a5a54' : '#9a9a94',
    fontFamily: 'DM Mono, monospace',
    watermark: false,
    dataZoom: { visible: true, position: 'top', height: 6, start: 0, end: 100 },
  });

  // Nom du symbole dans le header HTML (pas dans le chart)
  const label = document.getElementById('chart-sym-label');
  if (label) label.textContent = sym || activeSymbol || '';
}

function renderPriceLine(symbol) {
  if (!chart || !candleHistory[symbol] || candleHistory[symbol].length === 0) return;
  const candles = candleHistory[symbol];
  const dark = document.documentElement.getAttribute('data-theme') === 'dark';

  chart.setMarketData(candles);

  const linePlots = {
    Price: {
      data: candles.map(c => ({ time: c.time, value: c.close })),
      options: {
        style: 'line',
        color: dark ? '#2ecc71' : '#1a7a4a',
        linewidth: 2,
      },
    },
  };
  priceLineIndicator = chart.addIndicator('Price', linePlots, { isOverlay: true });
}

function addTradeToChart(symbol, price, volume) {
  if (symbol !== activeSymbol) return;
  if (!candleHistory[symbol]) candleHistory[symbol] = [];

  const now = Date.now();
  const minuteTs = Math.floor(now / 60000) * 60000;
  const candles = candleHistory[symbol];
  const last = candles[candles.length - 1];

  if (last && last.time === minuteTs) {
    last.high   = Math.max(last.high, price);
    last.low    = Math.min(last.low,  price);
    last.close  = price;
    last.volume += volume;
  } else {
    candles.push({ time: minuteTs, open: price, high: price, low: price, close: price, volume });
    if (candles.length > 500) candles.shift();
  }

  // Update temps réel sans full re-render
  if (chart && chart.chart) {
    try {
      const bar = candles[candles.length - 1];
      if (priceLineIndicator) {
        priceLineIndicator.updateData({ Price: { data: [{ time: bar.time, value: bar.close }] } });
      }
      chart.updateData([bar]);
    } catch(e) { console.warn('[CHART] updateData skipped:', e.message); }
  }

  // Stats bar
  updateStatsBar(candles);
}

// ─────────────────────────────────────────────────────────────────
//  SYMBOL TABS
// ─────────────────────────────────────────────────────────────────
function initSymbolTabs() {
  document.querySelectorAll('.symbol-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.symbol-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      activeSymbol = tab.dataset.sym;
      document.getElementById('orderSym').value = activeSymbol;
      document.getElementById('book-sym').textContent = activeSymbol;
      updateSummary();
      loadHistoricalData(activeSymbol);
      if (candleHistory[activeSymbol]) updateStatsBar(candleHistory[activeSymbol]);
    });
  });
}

function updateStatsBar(candles) {
  if (!candles || candles.length === 0) return;
  const first = candles[0];
  const last  = candles[candles.length - 1];
  const high  = Math.max(...candles.map(c => c.high));
  const low   = Math.min(...candles.map(c => c.low));
  const change = last.close - first.open;
  const changePct = (change / first.open * 100);
  const changeStr = (change >= 0 ? '+' : '') + fmtPrice(change) + ' (' + (changePct >= 0 ? '+' : '') + changePct.toFixed(2) + '%)';

  document.getElementById('stat-last').textContent = fmtPrice(last.close);
  document.getElementById('stat-open').textContent = fmtPrice(first.open);
  document.getElementById('stat-high').textContent = fmtPrice(high);
  document.getElementById('stat-low').textContent  = fmtPrice(low);
  const changeEl = document.getElementById('stat-change');
  if (changeEl) {
    changeEl.textContent = changeStr;
    changeEl.className = 'stat-value ' + (change >= 0 ? 'up' : 'down');
  }
}

function updateSymbolPrice(symbol, price) {
  const el = document.getElementById('price-' + symbol);
  if (el) {
    el.textContent = fmtPrice(price);
    el.className = 'symbol-price up'; // TODO: compare to previous
  }
}

function renderSymbolTabs(symbols) {
  const container = document.getElementById('symbol-bar');
  container.innerHTML = '';
  symbols.forEach(s => {
    const tab = document.createElement('div');
    tab.className = 'symbol-tab' + (s.name === activeSymbol ? ' active' : '');
    tab.dataset.sym = s.name;
    tab.textContent = s.name;
    tab.addEventListener('click', () => {
      document.querySelectorAll('.symbol-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      activeSymbol = s.name;
      document.getElementById('orderSym').value = activeSymbol;
      document.getElementById('book-sym').textContent = activeSymbol;
      updateSummary();
      loadHistoricalData(activeSymbol);
    });
    container.appendChild(tab);
  });
} 

// ─────────────────────────────────────────────────────────────────
//  ORDER FORM
// ─────────────────────────────────────────────────────────────────
function setOrderSide(side) {
  currentSide = side;
  document.querySelectorAll('.order-tab').forEach(t => t.classList.remove('active'));
  document.querySelector(`.order-tab.${side}`).classList.add('active');
  const btn = document.getElementById('submitBtn');
  btn.className = `btn-submit ${side}`;
  btn.textContent = `${side.charAt(0).toUpperCase() + side.slice(1)} ${activeSymbol}`;
  updateSummary();
}

function updateSummary() {
  const price = parseFloat(document.getElementById('orderPrice').value);
  const qty   = parseFloat(document.getElementById('orderQty').value);
  document.getElementById('summaryTotal').textContent = '$' + (price * qty).toFixed(2);
  document.getElementById('submitBtn').textContent =
    `${currentSide.charAt(0).toUpperCase() + currentSide.slice(1)} ${activeSymbol}`;
}

function stepInput(id, dir) {
  const el = document.getElementById(id);
  const step = parseFloat(el.step) || 1;
  const val = parseFloat(el.value) || 0;
  const min = parseFloat(el.min);
  let next = Math.round((val + dir * step) * 10000) / 10000;
  if (!isNaN(min)) next = Math.max(min, next);
  el.value = next;
  updateSummary();
}

function placeOrder() {
  const price = parseFloat(document.getElementById('orderPrice').value);
  const vol   = parseFloat(document.getElementById('orderQty').value);
  const sym   = document.getElementById('orderSym').value;

  let apiSide = currentSide === 'buy' ? 'B' : 'S';

  if (!price || !vol || !sym) return;

  fetch(`/post-order?key=${userKey}&sym=${sym}&side=${apiSide}&price=${price}&vol=${vol}`)
  .then(r => r.json())
  .then(data => console.log('[ORDER]', data))
  .catch(err => console.error('[ORDER ERROR]', err));
}
// ─────────────────────────────────────────────────────────────────
//  SESSION BADGE
// ─────────────────────────────────────────────────────────────────
function updateSessionBadge(connected) {
  const badge = document.querySelector('.session-badge');
  if (!badge) return;
  badge.textContent = connected ? '' : 'OFFLINE';
  badge.style.background = connected ? 'var(--green-bg)' : 'var(--red-bg)';
  badge.style.color       = connected ? 'var(--green)'    : 'var(--red)';
}

// ─────────────────────────────────────────────────────────────────
//  HISTORICAL DATA
// ─────────────────────────────────────────────────────────────────
async function loadHistoricalData(symbol) {
  try {
    const res = await fetch(`/data/${symbol}`);
    const data = await res.json();
    if (!Array.isArray(data)) {
      console.warn(`[CHART] No CSV data for ${symbol}`);
      return;
    }
    candleHistory[symbol] = data.map(d => ({
      time:   new Date(d.time).getTime(),
      open:   d.close,
      high:   d.close,
      low:    d.close,
      close:  d.close,
      volume: 0
    }));
    // Mettre à jour le prix dans le tab + stats bar avec les données CSV
    const hist = candleHistory[symbol];
    const last = hist[hist.length - 1];
    const first = hist[0];
    if (last) updateSymbolPrice(symbol, last.close);
    if (symbol === activeSymbol && last && first) updateStatsBar(hist);

    if (symbol === activeSymbol) {
      initChart(symbol);
      renderPriceLine(symbol);
    }
  } catch(e) {
    console.error('[CHART] Failed to load data for', symbol, e);
  }
}

// ─────────────────────────────────────────────────────────────────
//  THEME
// ─────────────────────────────────────────────────────────────────
function toggleTheme() {
  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  const next = isDark ? 'light' : 'dark';
  applyTheme(next);
  localStorage.setItem('theme', next);
}

function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  const btn = document.getElementById('theme-toggle');
  if (btn) btn.textContent = theme === 'dark' ? '☀ light' : '☾ dark';

  // Re-init chart avec les bonnes couleurs
  if (activeSymbol) {
    initChart(activeSymbol);
    renderPriceLine(activeSymbol);
  }
}

// ─────────────────────────────────────────────────────────────────
//  UTILS
// ─────────────────────────────────────────────────────────────────
function fmtPrice(p) {
  if (p === undefined || p === null) return '—';
  return p < 10 ? p.toFixed(4) : p.toFixed(2);
}

// ─────────────────────────────────────────────────────────────────
//  INIT
// ─────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const savedTheme = localStorage.getItem('theme') || 'light';
  document.documentElement.setAttribute('data-theme', savedTheme);
  const btn = document.getElementById('theme-toggle');
  if (btn) btn.textContent = savedTheme === 'dark' ? '☀ light' : '☾ dark';

  initSymbolTabs();
  symbols.forEach(sym => loadHistoricalData(sym));
  if (!activeSymbol) initChart();
  console.log("Activesym: " + activeSymbol)
  if (activeSymbol) {
    document.getElementById('orderSym').value   = activeSymbol;
    document.getElementById('book-sym').textContent = activeSymbol;
    document.getElementById('submitBtn').textContent = `Buy ${activeSymbol}`;
  }
});
