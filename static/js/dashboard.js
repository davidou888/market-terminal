// ──────────────────────────────────────────────────────────────────
//  INITIAL STATE
//  `initSymbols` is injected by Jinja2 from the Flask route.
//  e.g. ["AAPL", "AMZN", "BINANCE:BTCUSDT"]
// ──────────────────────────────────────────────────────────────────
const initSymbols = window.SYMBOLS;

// Maximum number of 1-min candles to keep per symbol in memory.
// Older candles are dropped from the left of the array.
const MAX_CANDLES = 500;

// Maximum log rows to display in the trade log.
const MAX_LOG_ROWS = 60;

// ──────────────────────────────────────────────────────────────────
//  PER-SYMBOL STATE
//  history[sym] = {
//    candles: [ {x: ms, o, h, l, c, v}, … ],  // sorted ascending by time
//    lastTrade: price,                           // last raw tick price
//    openPrice: price,                           // first price seen (for % chg)
//  }
// ──────────────────────────────────────────────────────────────────
const history = {};

// Currently displayed symbol
let activeSymbol = initSymbols[0] || null;

// Favourites: Set of symbol strings, persisted in localStorage
const FAV_KEY = 'mkt_favourites';
let favourites = new Set(JSON.parse(localStorage.getItem(FAV_KEY) || '[]'));

// ──────────────────────────────────────────────────────────────────
//  UTILITIES
// ──────────────────────────────────────────────────────────────────

/** Convert a symbol string to a valid HTML id fragment (no colons/spaces). */
function safeId(sym) { return sym.replace(/:/g, '-').replace(/\s/g, '_'); }

/** Format a price with appropriate decimal places. */
function fmtPrice(p) { return p < 10 ? p.toFixed(4) : p.toFixed(2); }

/** Format a large volume number compactly (e.g. 1 234 567 → "1.2M"). */
function fmtVol(v) {
  if (v >= 1e6) return (v / 1e6).toFixed(1) + 'M';
  if (v >= 1e3) return (v / 1e3).toFixed(0) + 'K';
  return v.toString();
}

/** Format a millisecond timestamp as HH:MM:SS. */
function fmtTime(ms) {
  return new Date(ms).toLocaleTimeString('en-GB', { hour12: false });
}

/** Show a brief toast message at top-right. */
function toast(msg, type = 'ok') {
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.textContent = msg;
  document.getElementById('toast-container').appendChild(el);
  setTimeout(() => el.remove(), 3000);
}

/** Persist the favourites Set to localStorage. */
function saveFavourites() {
  localStorage.setItem(FAV_KEY, JSON.stringify([...favourites]));
}

// ──────────────────────────────────────────────────────────────────
//  CLOCK
// ──────────────────────────────────────────────────────────────────
function tickClock() {
  document.getElementById('clock').textContent =
    new Date().toLocaleTimeString('en-GB', { hour12: false });
}
tickClock();
setInterval(tickClock, 1000);

// ──────────────────────────────────────────────────────────────────
//  CHART  (ApexCharts candlestick)
// ──────────────────────────────────────────────────────────────────

/*
 * ApexCharts candlestick series data format:
 *   [ { x: <Date|ms>, y: [open, high, low, close] }, … ]
 *
 * We store candles internally as:
 *   { x: ms, o, h, l, c, v }
 * and convert to ApexCharts format on render.
 */

const chartOptions = {
  chart: {
    id: 'candlestick',
    type: 'candlestick',
    height: '100%',
    background: 'transparent',
    toolbar: { show: true, tools: { download: false, selection: true, zoom: true, zoomin: true, zoomout: true, pan: true, reset: true } },
    animations: { enabled: false },    // disable for performance with many candles
    foreColor: '#637d8f',
  },
  // Candlestick colours
  plotOptions: {
    candlestick: {
      colors: { upward: '#26a69a', downward: '#ef5350' },
      wick: { useFillColor: true },
    }
  },
  xaxis: {
    type: 'datetime',
    labels: {
      style: { fontFamily: "'IBM Plex Mono', monospace", fontSize: '10px', colors: '#637d8f' },
      datetimeUTC: false,
    },
    axisBorder: { color: '#1a2230' },
    axisTicks:  { color: '#1a2230' },
  },
  yaxis: {
    opposite: true,    // price axis on the right (Bloomberg-style)
    labels: {
      style: { fontFamily: "'IBM Plex Mono', monospace", fontSize: '10px', colors: '#637d8f' },
      formatter: v => fmtPrice(v),
    },
  },
  grid: {
    borderColor: '#1a2230',
    strokeDashArray: 3,
  },
  tooltip: {
    theme: 'dark',
    style: { fontFamily: "'IBM Plex Mono', monospace", fontSize: '11px' },
    // Custom tooltip showing OHLCV
    custom({ seriesIndex, dataPointIndex, w }) {
      const d = w.globals.initialSeries[0].data[dataPointIndex];
      if (!d) return '';
      const [o, h, l, c] = d.y;
      const ts = new Date(d.x).toLocaleString('en-GB', { hour12: false });
      const col = c >= o ? '#26a69a' : '#ef5350';
      return `<div style="padding:8px 12px;font-family:var(--mono);font-size:11px;background:#0c0f15;border:1px solid #1a2230">
        <div style="color:#637d8f;margin-bottom:4px">${ts}</div>
        <div>O <span style="color:${col}">${fmtPrice(o)}</span></div>
        <div>H <span style="color:${col}">${fmtPrice(h)}</span></div>
        <div>L <span style="color:${col}">${fmtPrice(l)}</span></div>
        <div>C <span style="color:${col}">${fmtPrice(c)}</span></div>
      </div>`;
    }
  },
  series: [{ name: 'Price', data: [] }],
  noData: {
    text: 'Waiting for data…',
    align: 'center',
    verticalAlign: 'middle',
    style: { color: '#3d5063', fontFamily: "'IBM Plex Mono', monospace", fontSize: '13px' },
  },
};

// Mount the chart once the DOM is ready
const chart = new ApexCharts(document.getElementById('apexchart'), chartOptions);
chart.render();

/**
 * Re-render the candlestick chart for `activeSymbol`.
 * Called after receiving new candles or switching symbols.
 */
function renderChart() {
  const h = history[activeSymbol];
  if (!h) return;

  // Convert internal format → ApexCharts format
  const series = h.candles.map(c => ({ x: c.x, y: [c.o, c.h, c.l, c.c] }));
  chart.updateSeries([{ name: activeSymbol, data: series }], false);

  // Update OHLCV stats bar with the latest candle
  const last = h.candles.at(-1);
  if (last) {
    document.getElementById('stat-o').textContent = fmtPrice(last.o);
    document.getElementById('stat-h').textContent = fmtPrice(last.h);
    document.getElementById('stat-l').textContent = fmtPrice(last.l);
    document.getElementById('stat-c').textContent = fmtPrice(last.c);
    document.getElementById('stat-v').textContent = fmtVol(last.v);
  }
}

// ──────────────────────────────────────────────────────────────────
//  TICKER BAR MANAGEMENT
// ──────────────────────────────────────────────────────────────────

/**
 * Add (or update) a card in the horizontal ticker bar.
 * If a card for `sym` already exists, skip creation.
 */
function ensureTickerCard(sym) {
  const id = safeId(sym);
  if (document.getElementById(`tc-${id}`)) return;  // already exists

  const bar  = document.getElementById('ticker-bar');
  const card = document.createElement('div');
  card.className = `tc${sym === activeSymbol ? ' active' : ''}`;
  card.id = `tc-${id}`;
  card.dataset.sym = sym;
  card.innerHTML = `
    <div class="tc-sym">${sym}</div>
    <div class="tc-price" id="tcp-${id}">—</div>
    <div class="tc-chg"   id="tcc-${id}">—</div>
    <span class="tc-star${favourites.has(sym) ? ' active' : ''}"
          id="star-${id}"
          title="Toggle favourite"
          onclick="toggleFav('${sym}', event)">★</span>`;
  // Click on the card body (not the star) selects the symbol
  card.addEventListener('click', () => selectSymbol(sym));
  bar.appendChild(card);
}

/**
 * Switch the active symbol and update chart + header.
 */
function selectSymbol(sym) {
  activeSymbol = sym;
  document.getElementById('chart-sym-label').textContent = sym;

  // Update active state on all cards
  document.querySelectorAll('.tc').forEach(c =>
    c.classList.toggle('active', c.dataset.sym === sym));
  // Update active state in fav list
  document.querySelectorAll('.fav-row').forEach(r =>
    r.classList.toggle('active-fav', r.dataset.sym === sym));

  // Show loading overlay if no candles yet
  const h = history[sym];
  const overlay = document.getElementById('loading-overlay');
  if (!h || h.candles.length === 0) {
    overlay.classList.remove('hidden');
  } else {
    overlay.classList.add('hidden');
    renderChart();
  }
}

/**
 * Update the price display on a ticker card.
 * `dir` is "up" or "down" (compared to previous price).
 */
function updateTickerCard(sym, price, dir) {
  const id = safeId(sym);
  const priceEl = document.getElementById(`tcp-${id}`);
  const chgEl   = document.getElementById(`tcc-${id}`);
  if (!priceEl) return;

  priceEl.textContent = fmtPrice(price);
  priceEl.className   = `tc-price ${dir}`;
  setTimeout(() => { priceEl.className = 'tc-price'; }, 400);

  // Show % change from open
  const h = history[sym];
  if (h && h.openPrice != null) {
    const pct = ((price - h.openPrice) / h.openPrice * 100).toFixed(2);
    chgEl.textContent = `${pct >= 0 ? '+' : ''}${pct}%`;
    chgEl.className   = `tc-chg ${pct >= 0 ? 'up' : 'down'}`;
  }
}

// ──────────────────────────────────────────────────────────────────
//  FAVOURITES
// ──────────────────────────────────────────────────────────────────

/**
 * Toggle a symbol in / out of the favourites set.
 * Stops click propagation so the ticker card isn't also selected.
 */
function toggleFav(sym, event) {
  event.stopPropagation();
  if (favourites.has(sym)) {
    favourites.delete(sym);
  } else {
    favourites.add(sym);
  }
  saveFavourites();

  // Sync star icon
  const id   = safeId(sym);
  const star = document.getElementById(`star-${id}`);
  if (star) star.classList.toggle('active', favourites.has(sym));

  renderFavList();
}

/**
 * Rebuild the favourites panel from the current state.
 * Called on: toggle, new price data for a favourite.
 */
function renderFavList() {
  const container = document.getElementById('fav-list');
  const empty     = document.getElementById('fav-empty');

  // Remove all existing fav rows (keep the empty placeholder)
  container.querySelectorAll('.fav-row').forEach(el => el.remove());

  if (favourites.size === 0) {
    empty.style.display = '';
    return;
  }
  empty.style.display = 'none';

  favourites.forEach(sym => {
    const h    = history[sym];
    const price = h?.lastTrade;
    const pct   = (h?.openPrice != null && price != null)
      ? ((price - h.openPrice) / h.openPrice * 100).toFixed(2)
      : null;
    const dir  = pct != null ? (pct >= 0 ? 'up' : 'down') : '';

    const row = document.createElement('div');
    row.className = `fav-row${sym === activeSymbol ? ' active-fav' : ''}`;
    row.dataset.sym = sym;
    row.innerHTML = `
      <span class="fav-sym">${sym}</span>
      <div class="fav-right">
        <div class="fav-price">${price != null ? fmtPrice(price) : '—'}</div>
        <div class="fav-chg ${dir}">${pct != null ? (pct >= 0 ? '+' : '') + pct + '%' : '—'}</div>
      </div>`;
    row.addEventListener('click', () => selectSymbol(sym));
    // Insert before the empty placeholder
    container.insertBefore(row, empty);
  });
}

// ──────────────────────────────────────────────────────────────────
//  CANDLE HELPERS
// ──────────────────────────────────────────────────────────────────

/**
 * Round a millisecond timestamp down to the start of its 1-min bar.
 * e.g. 13:47:23 → 13:47:00
 */
function barKey(ms) { return Math.floor(ms / 60000) * 60000; }

/**
 * Insert or merge a candle into history[sym].candles.
 *
 * If a candle with the same bar timestamp already exists, update its
 * high, low, close, and volume (merge). Otherwise append a new candle.
 * Trim the array to MAX_CANDLES entries.
 */
function upsertCandle(sym, candle) {
  if (!history[sym]) {
    history[sym] = { candles: [], lastTrade: null, openPrice: null };
  }
  const h    = history[sym];
  const bars = h.candles;
  const bk   = barKey(candle.x);

  // Search from the end first (most common case: updating the latest bar)
  let idx = bars.length - 1;
  while (idx >= 0 && bars[idx].x > bk) idx--;

  if (idx >= 0 && bars[idx].x === bk) {
    // Existing bar — update OHLCV in-place
    const b = bars[idx];
    b.h = Math.max(b.h, candle.h);
    b.l = Math.min(b.l, candle.l);
    b.c = candle.c;
    b.v += candle.v;
  } else {
    // New bar — insert at the right position (ascending order)
    bars.splice(idx + 1, 0, {
      x: bk, o: candle.o, h: candle.h, l: candle.l, c: candle.c, v: candle.v
    });
    if (bars.length > MAX_CANDLES) bars.shift();
  }

  // Track open price (first price ever seen for % change calculation)
  if (h.openPrice === null && bars.length > 0) h.openPrice = bars[0].o;
}

// ──────────────────────────────────────────────────────────────────
//  SOCKET.IO — event handlers
// ──────────────────────────────────────────────────────────────────
const socket = io();

/* Connection established */
socket.on('connect', () => {
  document.getElementById('conn-dot').classList.add('live');
  document.getElementById('conn-label').textContent = 'LIVE';
});

/* Connection lost */
socket.on('disconnect', () => {
  document.getElementById('conn-dot').classList.remove('live');
  document.getElementById('conn-label').textContent = 'DISCONNECTED';
});

/**
 * `candle` event — a completed or in-progress 1-min OHLCV bar.
 * Emitted in bulk for historical data and individually for live updates.
 *
 * Payload: { symbol, time, open, high, low, close, volume }
 */
socket.on('history_batch', data => {
  const sym = data.symbol;

  // Make sure a ticker card exists in the bar for this symbol.
  // On initial load the cards are pre-created, but if the user
  // added a new symbol at runtime this might be the first time we see it.
  ensureTickerCard(sym);

  // Insert every candle from the batch into our in-memory history store.
  // upsertCandle() handles two cases:
  //   - a timestamp we haven't seen before → appends a new bar
  //   - a timestamp we already have       → merges H/L/C/V into the existing bar
  // We do this in a plain loop WITHOUT calling renderChart() each iteration —
  // that's the key difference from the old approach which re-rendered the
  // ApexCharts instance hundreds of times and froze the tab.
  data.candles.forEach(c => {
    upsertCandle(sym, {
      x: c.time,          // milliseconds timestamp (bar key)
      o: c.open,
      h: c.high,
      l: c.low,
      c: c.close,
      v: c.volume,
    });
  });

  // Now that all candles are loaded, update the ticker card once
  // using the very last candle as the "current price"
  const h = history[sym];
  if (h && h.candles.length > 0) {
    const last = h.candles.at(-1);   // most recent bar

    // lastTrade drives the price shown on the ticker card
    h.lastTrade = last.c;

    // openPrice is the baseline for % change calculation.
    // Only set it if it hasn't been set yet (don't overwrite if live trades
    // already arrived before the history batch finished)
    if (h.openPrice === null) h.openPrice = h.candles[0].o;

    updateTickerCard(sym, last.c, 'up');
  }

  // Render the chart once — now that ALL candles are in memory
  // This is the single chart update for the entire historical dataset
  if (sym === activeSymbol) renderChart();

  // Refresh the favourites sidebar if this symbol is starred
  if (favourites.has(sym)) renderFavList();
});

/**
 * `history_done` event — server has finished sending historical candles
 * for a given symbol. Hide the loading overlay if it's the active symbol.
 *
 * Payload: { symbol }
 */
socket.on('history_done', data => {
  if (data.symbol === activeSymbol) {
    document.getElementById('loading-overlay').classList.add('hidden');
    renderChart();
  }
});

/**
 * `trade` event — a single raw tick from Finnhub.
 * We aggregate it into the current 1-min candle client-side.
 *
 * Payload: { symbol, price, volume, time }
 */
socket.on('trade', data => {
  const { symbol, price, volume, time } = data;
  ensureTickerCard(symbol);

  if (!history[symbol]) {
    history[symbol] = { candles: [], lastTrade: null, openPrice: null };
  }
  const h = history[symbol];

  // Merge this tick into the current bar
  const bk = barKey(time);
  const bars = h.candles;
  const lastBar = bars.at(-1);

  if (lastBar && lastBar.x === bk) {
    // Update existing bar
    lastBar.h = Math.max(lastBar.h, price);
    lastBar.l = Math.min(lastBar.l, price);
    lastBar.c = price;
    lastBar.v += volume;
  } else {
    // Open a new bar
    bars.push({ x: bk, o: price, h: price, l: price, c: price, v: volume });
    if (bars.length > MAX_CANDLES) bars.shift();
  }
  if (h.openPrice === null && bars.length) h.openPrice = bars[0].o;

  // Update ticker card
  const prev = h.lastTrade;
  const dir  = prev == null || price >= prev ? 'up' : 'down';
  h.lastTrade = price;
  updateTickerCard(symbol, price, dir);

  if (symbol === activeSymbol) renderChart();
  if (favourites.has(symbol)) renderFavList();

  // ── Trade log row ──
  const wrap = document.getElementById('log-table-wrap');
  const pct  = h.openPrice ? ((price - h.openPrice) / h.openPrice * 100).toFixed(2) : null;
  const row  = document.createElement('div');
  row.className = 'log-row';
  row.innerHTML = `
    <span class="col-time">${fmtTime(time)}</span>
    <span class="col-sym">${symbol}</span>
    <span class="col-price ${dir}">${fmtPrice(price)}</span>
    <span class="col-chg ${dir}">${pct != null ? (pct >= 0 ? '+' : '') + pct + '%' : '—'}</span>
    <span class="col-vol">${fmtVol(volume)}</span>`;
  // Insert after the sticky header
  wrap.insertBefore(row, wrap.children[1]);
  if (wrap.children.length > MAX_LOG_ROWS + 1) wrap.removeChild(wrap.lastChild);
});

/**
 * `symbol_ack` event — server response to a `subscribe_symbol` request.
 * Payload: { symbol, ok, error?, already? }
 */
socket.on('symbol_ack', data => {
  const btn    = document.getElementById('sym-add-btn');
  const status = document.getElementById('add-status');
  btn.disabled = false;

  if (data.ok) {
    const msg = data.already
      ? `${data.symbol} already tracked — history refreshed`
      : `${data.symbol} added successfully`;
    status.textContent = msg;
    status.className   = 'ok';
    toast(msg, 'ok');
    // Switch to the newly added symbol
    selectSymbol(data.symbol);
  } else {
    const msg = `Failed: ${data.error || 'unknown error'}`;
    status.textContent = msg;
    status.className   = 'err';
    toast(msg, 'err');
  }

  // Clear status message after 4 seconds
  setTimeout(() => { status.textContent = ''; status.className = ''; }, 4000);
});

// ──────────────────────────────────────────────────────────────────
//  ADD SYMBOL  — user input → server subscription
// ──────────────────────────────────────────────────────────────────

function submitSymbol() {
  const input  = document.getElementById('sym-input');
  const btn    = document.getElementById('sym-add-btn');
  const status = document.getElementById('add-status');
  const sym    = input.value.trim().toUpperCase();

  if (!sym) return;

  // Show loading state
  btn.disabled  = true;
  btn.innerHTML = '<span class="spinner"></span>';
  status.textContent = `Requesting ${sym}…`;
  status.className   = '';

  // Emit subscription request to the server
  socket.emit('subscribe_symbol', { symbol: sym });

  // Reset button text after 500ms (the ack resets disabled state)
  setTimeout(() => { btn.innerHTML = '+'; }, 600);
  input.value = '';
}

document.getElementById('sym-add-btn').addEventListener('click', submitSymbol);
document.getElementById('sym-input').addEventListener('keydown', e => {
  if (e.key === 'Enter') submitSymbol();
});

// ──────────────────────────────────────────────────────────────────
//  INITIALISE
//  Create ticker cards for the initial symbol list injected by Flask
//  and initialise history objects before any events arrive.
// ──────────────────────────────────────────────────────────────────

initSymbols.forEach(sym => {
  history[sym] = { candles: [], lastTrade: null, openPrice: null };
  ensureTickerCard(sym);
});

// Set the chart title to the first symbol
if (activeSymbol) {
  document.getElementById('chart-sym-label').textContent = activeSymbol;
}

// Render the initial (empty) fav list
renderFavList();