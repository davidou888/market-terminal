// ─────────────────────────────────────────────────────────────────
//  dashboard.js — market-terminal
//  Connects the UI to Flask-SocketIO backend
// ─────────────────────────────────────────────────────────────────

const SYMBOLS     = ["GOOGL", "AMZN"];
let activeSymbol  = SYMBOLS[0];
let currentSide   = 'buy';
let userKey       = sessionStorage.getItem('api_key');
let cashBalance   = 10000;

// Per-symbol candle history for QFChart
const candleHistory = {}; // { sym: [{time, open, high, low, close, volume}] }


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

// ─────────────────────────────────────────────────────────────────
//  CHART (QFChart candlestick)
// ─────────────────────────────────────────────────────────────────
let chart = null;

function initChart() {
  const el = document.getElementById('qf-mount');
  if (!el || typeof QFChart === 'undefined') return;
  // Init with empty data
  chart = new QFChart({
    container: el,
    theme: 'light',
    data: [],
  });
}

function addTradeToChart(symbol, price, volume) {
  if (symbol !== activeSymbol) return;
  if (!candleHistory[symbol]) candleHistory[symbol] = [];

  const now = Date.now();
  const minuteTs = Math.floor(now / 60000) * 60000;
  const candles = candleHistory[symbol];
  const last = candles[candles.length - 1];

  if (last && last.time === minuteTs) {
    // Update current candle
    last.high  = Math.max(last.high, price);
    last.low   = Math.min(last.low,  price);
    last.close = price;
    last.volume += volume;
  } else {
    // New candle
    candles.push({ time: minuteTs, open: price, high: price, low: price, close: price, volume });
    if (candles.length > 500) candles.shift();
  }

  if (chart) chart.setData(candles);

  // Update stats bar
  const c = candles[candles.length - 1];
  document.getElementById('stat-last').textContent = fmtPrice(c.close);
  document.getElementById('stat-open').textContent = fmtPrice(c.open);
  document.getElementById('stat-high').textContent = fmtPrice(c.high);
  document.getElementById('stat-low').textContent  = fmtPrice(c.low);
  document.getElementById('stat-vol').textContent  = c.volume;
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
    });
  });
}

function updateSymbolPrice(symbol, price) {
  const el = document.getElementById('price-' + symbol);
  if (el) {
    el.textContent = fmtPrice(price);
    el.className = 'symbol-price up'; // TODO: compare to previous
  }
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
//  TIMER
// ─────────────────────────────────────────────────────────────────
let sessionSeconds = 10 * 60;

function startTimer() {
  setInterval(() => {
    if (sessionSeconds <= 0) return;
    sessionSeconds--;
    const m = Math.floor(sessionSeconds / 60).toString().padStart(2, '0');
    const s = (sessionSeconds % 60).toString().padStart(2, '0');
    document.getElementById('timer').textContent = `${m}:${s}`;
  }, 1000);
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
  initSymbolTabs();
  initChart();
  startTimer();
  console.log("Activesym: " + activeSymbol)
  if (activeSymbol) {
    document.getElementById('orderSym').value   = activeSymbol;
    document.getElementById('book-sym').textContent = activeSymbol;
    document.getElementById('submitBtn').textContent = `Buy ${activeSymbol}`;
  }
});
