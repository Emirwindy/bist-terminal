from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import yfinance as yf
import os

app = FastAPI()

# Ana sayfaya girildiğinde HTML dosyasını göster
@app.get("/")
async def read_root():
    # Dosya yolu kontrolü
    html_file = "index (3).html"
    if os.path.exists(html_file):
        return FileResponse(html_file)
    return {"status": "ok", "message": "BIST Terminal backend calisiyor fakat index (3).html bulunamadi."}

# Canlı BIST verilerini çeken API ucu
@app.get("/api/data")
async def get_stock_data():
    try:
        # Örnek olarak takip edilen BIST hisseleri
        tickers = ["THYAO.IS", "AKBNK.IS", "SASA.IS", "EREGL.IS", "GARAN.IS"]
        data = {}
        
        for ticker in tickers:
            stock = yf.Ticker(ticker)
            info = stock.fast_info
            data[ticker.replace(".IS", "")] = {
                "price": round(info.last_price, 2) if info.last_price else 0,
                "previousClose": round(info.previous_close, 2) if info.previous_close else 0
            }
            
        return {"status": "success", "data": data}
    except Exception as e:
        return {"status": "error", "message": str(e)}
