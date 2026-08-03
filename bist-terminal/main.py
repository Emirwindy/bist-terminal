from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import yfinance as yf

app = FastAPI()

# Sen kopyala-yapıştırla uğraşma diye orijinal arayüzünün kodunu direkt buraya gömdüm
html_content = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BIST Terminali</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/lucide@latest"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://unpkg.com/lightweight-charts/dist/lightweight-charts.standalone.production.js"></script>
    <style>
        body { background-color: #0b0e14; color: #c5c7d0; font-family: 'Inter', sans-serif; }
        .grid-bg { background-image: radial-gradient(#1f293d 1px, transparent 1px); background-size: 16px 16px; }
        .custom-scrollbar::-webkit-scrollbar { width: 4px; height: 4px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: #0b0e14; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: #1f293d; border-radius: 2px; }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #374151; }
    </style>
</head>
<body class="h-screen flex flex-col overflow-hidden grid-bg select-none">
    <header class="h-12 border-b border-gray-800 bg-[#0f131c] flex items-center justify-between px-4 z-10">
        <div class="flex items-center space-x-3">
            <div class="flex items-center space-x-2">
                <i data-lucide="candlestick-chart" class="w-5 h-5 text-emerald-500"></i>
                <span class="font-bold text-white tracking-wider text-sm">BIST<span class="text-emerald-500">TERMINAL</span></span>
            </div>
            <span class="text-xs px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">LIVE v1.0</span>
        </div>
        <div class="flex items-center space-x-6 text-xs font-mono">
            <div class="flex items-center space-x-2"><span class="text-gray-500">XU100:</span><span class="text-emerald-400 font-bold">9,850.20</span><span class="text-emerald-500 text-[10px]">+1.2%</span></div>
            <div class="flex items-center space-x-2"><span class="text-gray-500">USD/TRY:</span><span class="text-white font-bold">32.85</span></div>
            <div class="flex items-center space-x-2"><div class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div><span class="text-gray-400">BAGLANTI AÇIK</span></div>
        </div>
    </header>

    <div class="flex-1 flex overflow-hidden">
        <aside class="w-64 border-r border-gray-800 bg-[#0f131c]/50 flex flex-col">
            <div class="p-3 border-b border-gray-800">
                <div class="relative">
                    <i data-lucide="search" class="w-4 h-4 absolute left-3 top-2.5 text-gray-500"></i>
                    <input type="text" id="symbolSearch" placeholder="Sembol Ara (örn: THYAO)..." class="w-full bg-[#161b26] text-xs text-white pl-9 pr-3 py-2 rounded border border-gray-800 focus:outline-none focus:border-emerald-500 font-mono">
                </div>
            </div>
            <div class="flex-1 overflow-y-auto custom-scrollbar" id="watchlist"></div>
        </aside>

        <main class="flex-1 flex flex-col bg-[#0b0e14]">
            <div class="h-14 border-b border-gray-800 px-6 flex items-center justify-between bg-[#0f131c]/30">
                <div class="flex items-center space-x-4">
                    <h1 id="selectedSymbol" class="text-xl font-bold text-white font-mono">THYAO</h1>
                    <span id="selectedName" class="text-xs text-gray-400">Türk Hava Yolları</span>
                    <div class="h-4 w-px bg-gray-800"></div>
                    <div class="font-mono"><span id="selectedPrice" class="text-lg font-bold text-emerald-400">302.50</span><span class="text-xs text-gray-500 ml-1">TRY</span></div>
                    <span id="selectedChange" class="text-xs px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 font-mono font-bold">+2.45%</span>
                </div>
            </div>
            <div class="flex-1 p-4 relative" id="chartContainer">
                <div id="tvChart" class="w-full h-full"></div>
            </div>
        </main>
    </div>

    <script>
        lucide.createIcons();
        const stocks = [
            { symbol: 'THYAO', name: 'Türk Hava Yolları', price: 302.50, change: 2.45 },
            { symbol: 'AKBNK', name: 'Akbank', price: 58.20, change: -0.85 },
            { symbol: 'GARAN', name: 'Garanti Bankası', price: 104.10, change: 1.12 },
            { symbol: 'EREGL', name: 'Ereğli Demir Çelik', price: 52.40, change: 0.00 },
            { symbol: 'SASA', name: 'Sasa Polyester', price: 46.80, change: -1.26 }
        ];

        function renderWatchlist() {
            const container = document.getElementById('watchlist');
            container.innerHTML = stocks.map(stock => `
                <div onclick="selectStock('${stock.symbol}')" class="p-3 border-b border-gray-800/50 hover:bg-[#161b26] cursor-pointer transition flex items-center justify-between group">
                    <div>
                        <div class="font-bold text-white text-xs font-mono group-hover:text-emerald-400">${stock.symbol}</div>
                        <div class="text-[10px] text-gray-500 truncate w-24">${stock.name}</div>
                    </div>
                    <div class="text-right font-mono">
                        <div class="text-xs text-white font-bold">${stock.price.toFixed(2)}</div>
                        <div class="text-[10px] ${stock.change >= 0 ? 'text-emerald-400' : 'text-rose-500'}">
                            ${stock.change >= 0 ? '+' : ''}${stock.change}%
                        </div>
                    </div>
                </div>
            `).join('');
        }

        let chart;
        function initChart() {
            const container = document.getElementById('tvChart');
            chart = LightweightCharts.createChart(container, {
                layout: { backgroundColor: '#0b0e14', textColor: '#9CA3AF' },
                grid: { vertLines: { color: '#1F2937' }, horzLines: { color: '#1F2937' } },
                timeScale: { borderColor: '#374151' }
            });
            const candlestickSeries = chart.addCandlestickSeries({
                upColor: '#10B981', downColor: '#EF4444', borderVisible: false, wickUpColor: '#10B981', wickDownColor: '#EF4444'
            });
            candlestickSeries.setData([
                { time: '2024-01-01', open: 290, high: 295, low: 288, close: 292 },
                { time: '2024-01-02', open: 292, high: 298, low: 291, close: 297 },
                { time: '2024-01-03', open: 297, high: 301, low: 295, close: 299 },
                { time: '2024-01-04', open: 299, high: 305, low: 298, close: 302.50 }
            ]);
            window.addEventListener('resize', () => { chart.applyOptions({ width: container.clientWidth, height: container.clientHeight }); });
        }

        function selectStock(symbol) {
            const stock = stocks.find(s => s.symbol === symbol);
            if (!stock) return;
            document.getElementById('selectedSymbol').innerText = stock.symbol;
            document.getElementById('selectedName').innerText = stock.name;
            document.getElementById('selectedPrice').innerText = stock.price.toFixed(2);
            document.getElementById('selectedChange').innerText = (stock.change >= 0 ? '+' : '') + stock.change + '%';
        }

        renderWatchlist();
        initChart();
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return html_content

@app.get("/api/data")
async def get_stock_data():
    try:
        tickers = ["THYAO.IS", "AKBNK.IS", "SASA.IS", "EREGL.IS", "GARAN.IS"]
        data = {}
        for ticker in tickers:
            stock = yf.Ticker(ticker)
            info = stock.fast_info
            symbol = ticker.replace(".IS", "")
            data[symbol] = {
                "price": round(info.last_price, 2) if info.last_price else 0,
                "previousClose": round(info.previous_close, 2) if info.previous_close else 0
            }
        return {"status": "success", "data": data}
    except Exception as e:
        return {"status": "error", "message": str(e)}
