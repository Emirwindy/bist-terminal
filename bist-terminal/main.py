from fastapi import FastAPI
from fastapi.responses import FileResponse
import yfinance as yf
import os

app = FastAPI()

# Ana sayfaya girildiğinde senin orijinal HTML dosyanı olduğu gibi basar
@app.get("/")
async def read_root():
    # Klasördeki index (3).html dosyasını arar
    if os.path.exists("index (3).html"):
        return FileResponse("index (3).html")
    elif os.path.exists("../index (3).html"):
        return FileResponse("../index (3).html")
    
    # İsmi değiştiyse klasördeki herhangi bir .html dosyasını yakalar
    for file in os.listdir("."):
        if file.endswith(".html"):
            return FileResponse(file)
            
    return {"status": "error", "message": "HTML dosyasi bulunamadi!"}

# Canlı BIST Veri API'si
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
