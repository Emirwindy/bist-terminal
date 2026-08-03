from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import yfinance as yf

app = FastAPI()

# HTML Kodun Tamamı Doğrudan Buradan Dönecek
html_content = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BIST Terminali</title>
    <style>
        body {
            background-color: #121212;
            color: #ffffff;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        .container {
            text-align: center;
            padding: 30px;
            background: #1e1e1e;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.5);
        }
        h1 { color: #00e676; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 BIST Terminali Canlıda!</h1>
        <p>Backend ve Arayüz Başarıyla Bağlandı.</p>
    </div>
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
