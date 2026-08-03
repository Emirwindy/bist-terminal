from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import yfinance as yf
import os

app = FastAPI()

# 1. Ana sayfaya girildiğinde HTML dosyasını otomatik bulup ekrana basar
@app.get("/")
async def read_root():
    # Klasördeki sonu .html ile biten ilk dosyayı yakalar (index (3).html dahil)
    for file in os.listdir("."):
        if file.endswith(".html"):
            return FileResponse(file)
    return {"status": "error", "message": "Klasörde HTML dosyası bulunamadı!"}

# 2. Canlı BIST Veri Çekme API'si
@app.get("/api/data")
async def get_stock_data():
    try:
        # BİST Takip Listesi
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
