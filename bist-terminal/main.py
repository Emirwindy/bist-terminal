from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import yfinance as yf
import uvicorn
import time as time_module

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

KAP_DATABASE = {
    "THYAO": [
        {"title": "THYAO - Filo Genişletme Açıklaması", "date": "14:20",
         "body": "Yeni geniş gövdeli uçak alımlarına ilişkin görüşmeler devam etmektedir."},
        {"title": "THYAO - Aylık Trafik Sonuçları", "date": "10:15",
         "body": "Yolcu doluluk oranları geçen yıla kıyasla artış gösterdi."}
    ],
    "SASA": [
        {"title": "SASA - Adana Tesis Yatırımı", "date": "11:45",
         "body": "PTA üretim tesisinde deneme üretimleri başladı."},
        {"title": "SASA - SPK Başvurusu", "date": "09:30",
         "body": "Sermaye artırımına ilişkin süreç tamamlanma aşamasındadır."}
    ]
}

# --- Zaman dilimi ayarları ---------------------------------------------------
# Her interval için Yahoo Finance'in izin verdiği makul period farklı.
# Örn: 1 dakikalık veri sadece son birkaç gün için mevcut, aşarsan Yahoo hata verir.
INTERVAL_PERIOD_MAP = {
    "1m":  "5d",
    "5m":  "1mo",
    "15m": "1mo",
    "60m": "3mo",
    "1d":  "6mo",
    "1wk": "2y",
    "1mo": "5y",
}
# Gün-içi (intraday) veriler saat bilgisi de taşımalı; günlük ve üzeri
# periyotlarda ise sadece tarih string'i kullanıyoruz (asağıdaki nota bakın).
INTRADAY_INTERVALS = {"1m", "5m", "15m", "60m"}


# --- Basit bellek-içi cache -------------------------------------------------
# Frontend her 10 saniyede bir soruyor ama Yahoo Finance'i bu kadar sık
# yormak hem gereksiz hem de IP'nin rate-limit yemesine (429) yol açabiliyor.
# Aynı hisse için CACHE_TTL saniye içinde gelen istekleri cache'ten cevaplıyoruz.
CACHE_TTL = 20  # saniye
_cache = {}


def get_cached_or_fetch(key, fetch_fn):
    now = time_module.time()
    cached = _cache.get(key)
    if cached and (now - cached["ts"] < CACHE_TTL):
        return cached["data"]
    data = fetch_fn()
    _cache[key] = {"data": data, "ts": now}
    return data


def calculate_sma(values, window):
    """Basit hareketli ortalama. Yeterli veri yoksa None döner."""
    sma = [None] * len(values)
    for i in range(window - 1, len(values)):
        window_slice = values[i - window + 1:i + 1]
        sma[i] = sum(window_slice) / window
    return sma


def get_live_price(stock, fallback):
    """fast_info üzerinden anlık fiyatı almaya çalışır, olmazsa son kapanışı kullanır."""
    try:
        fi = stock.fast_info
        price = None
        for key in ("last_price", "lastPrice"):
            try:
                price = fi[key]
                if price:
                    break
            except (KeyError, TypeError):
                price = getattr(fi, key, None)
                if price:
                    break
        if price is None:
            return fallback
        return round(float(price), 2)
    except Exception:
        return fallback


def get_daily_change_pct(stock, live_price):
    """Bir önceki kapanışa göre günlük % değişimi hesaplar (grafik periyodundan
    bağımsız olarak her zaman günlük bazda - kullanıcının seçtiği 1dk/1s gibi
    periyot ne olursa olsun 'günlük %' anlamlı kalsın diye)."""
    try:
        daily = stock.history(period="5d", interval="1d")
        closes = daily["Close"].dropna()
        if len(closes) >= 2:
            prev_close = float(closes.iloc[-2])
        elif len(closes) == 1:
            prev_close = float(closes.iloc[-1])
        else:
            return 0.0
        if not prev_close:
            return 0.0
        return round(((live_price - prev_close) / prev_close) * 100, 2)
    except Exception:
        return 0.0


@app.get("/")
def root():
    return {"status": "ok", "message": "BIST Terminal backend calisiyor"}


# Frontend'deki arama listesiyle birebir aynı tutulmalı
WATCHLIST_STOCKS = [
    {"code": "THYAO", "name": "Türk Hava Yolları"},
    {"code": "SASA", "name": "Sasa Polyester"},
    {"code": "EREGL", "name": "Ereğli Demir Çelik"},
    {"code": "TUPRS", "name": "Tüpraş"},
    {"code": "AKBNK", "name": "Akbank"},
    {"code": "GARAN", "name": "Garanti BBVA"},
    {"code": "ISCTR", "name": "İş Bankası (C)"},
    {"code": "ASELS", "name": "Aselsan"},
    {"code": "KCHOL", "name": "Koç Holding"},
    {"code": "BIMAS", "name": "BİM Mağazalar"},
    {"code": "SAHOL", "name": "Sabancı Holding"},
    {"code": "PGSUS", "name": "Pegasus"},
    {"code": "YKBNK", "name": "Yapı Kredi"},
    {"code": "VAKBN", "name": "VakıfBank"},
    {"code": "HALKB", "name": "Halkbank"},
    {"code": "TCELL", "name": "Turkcell"},
    {"code": "TTKOM", "name": "Türk Telekom"},
    {"code": "FROTO", "name": "Ford Otosan"},
    {"code": "TOASO", "name": "Tofaş Oto"},
    {"code": "ARCLK", "name": "Arçelik"},
    {"code": "PETKM", "name": "Petkim"},
    {"code": "KOZAL", "name": "Koza Altın"},
    {"code": "KOZAA", "name": "Koza Madencilik"},
    {"code": "SISE", "name": "Şişecam"},
    {"code": "MGROS", "name": "Migros"},
    {"code": "ULKER", "name": "Ülker Bisküvi"},
    {"code": "VESTL", "name": "Vestel"},
    {"code": "ENKAI", "name": "Enka İnşaat"},
    {"code": "TAVHL", "name": "TAV Havalimanları"},
    {"code": "ALARK", "name": "Alarko Holding"},
    {"code": "DOHOL", "name": "Doğan Holding"},
    {"code": "GUBRF", "name": "Gübre Fabrikaları"},
    {"code": "KRDMD", "name": "Kardemir (D)"},
    {"code": "OYAKC", "name": "Oyak Çimento"},
    {"code": "CCOLA", "name": "Coca-Cola İçecek"},
    {"code": "AEFES", "name": "Anadolu Efes"},
    {"code": "SOKM", "name": "Şok Marketler"},
    {"code": "HEKTS", "name": "Hektaş"},
]

WATCHLIST_TTL = 30  # saniye - 35 hisseyi her istek için tek tek çekmemek adına
_watchlist_cache = {"data": None, "ts": 0}


@app.get("/api/watchlist")
def get_watchlist():
    now = time_module.time()
    if _watchlist_cache["data"] and (now - _watchlist_cache["ts"] < WATCHLIST_TTL):
        return _watchlist_cache["data"]

    yf_symbols = [item["code"] + ".IS" for item in WATCHLIST_STOCKS]

    try:
        # 35 hisseyi tek tek istemek yerine yfinance'in toplu indirme
        # özelliğiyle tek seferde çekiyoruz - hem hızlı hem rate-limit dostu.
        df = yf.download(
            tickers=" ".join(yf_symbols),
            period="5d",
            interval="1d",
            group_by="ticker",
            progress=False,
            threads=True,
        )
    except Exception as e:
        return {"error": f"Watchlist verisi alınamadı: {str(e)}"}

    results = []
    for item in WATCHLIST_STOCKS:
        yf_symbol = item["code"] + ".IS"
        try:
            sub = df[yf_symbol] if len(yf_symbols) > 1 else df
            closes = sub["Close"].dropna()
            if len(closes) == 0:
                continue
            last_close = float(closes.iloc[-1])
            prev_close = float(closes.iloc[-2]) if len(closes) > 1 else last_close
            change_pct = ((last_close - prev_close) / prev_close * 100) if prev_close else 0.0
            results.append({
                "code": item["code"],
                "name": item["name"],
                "price": round(last_close, 2),
                "change_pct": round(change_pct, 2),
            })
        except Exception:
            continue  # tek bir hisse başarısız olsa da listenin geri kalanı bozulmasın

    response = {"stocks": results}
    _watchlist_cache["data"] = response
    _watchlist_cache["ts"] = now
    return response


@app.get("/api/stock/{symbol}")
def get_stock(symbol: str, interval: str = "1d"):
    # Kullanıcı "THYAO" ya da "THYAO.IS" yazmış olabilir, ikisini de tekilleştir
    clean_ticker = symbol.upper().replace(".IS", "").strip()
    yf_ticker = clean_ticker + ".IS"

    if not clean_ticker:
        return {"error": "Geçersiz hisse kodu."}

    # Bilinmeyen/geçersiz bir interval gelirse günlüğe düş
    clean_interval = interval if interval in INTERVAL_PERIOD_MAP else "1d"
    period = INTERVAL_PERIOD_MAP[clean_interval]
    is_intraday = clean_interval in INTRADAY_INTERVALS
    cache_key = f"{yf_ticker}:{clean_interval}"

    def fetch():
        stock = yf.Ticker(yf_ticker)
        df = stock.history(period=period, interval=clean_interval)

        if df.empty:
            return {"error": f"'{clean_ticker}' için '{clean_interval}' periyodunda veri bulunamadı."}

        # ÖNEMLİ FIX: lightweight-charts, verinin zaman sırasına göre artan ve
        # TEKİL olmasını şart koşar. Yahoo Finance özellikle gün-içi (60m, 15m vb.)
        # periyotlarda ara sıra tekrarlayan veya sırasız zaman damgaları
        # döndürebiliyor; bu durumda grafik hiçbir hata vermeden mumları
        # göstermeyi reddediyordu (boş grafik sorununun sebebi buydu).
        df = df[~df.index.duplicated(keep="last")].sort_index()

        candles = []
        closes = []
        for idx, row in df.iterrows():
            if is_intraday:
                # Gün-içi mumlarda saat bilgisi de gerekiyor, bu yüzden gerçek
                # zaman anını temsil eden unix timestamp kullanıyoruz (bu, günlük
                # mumlardaki tarih kayması sorununa yol açmaz çünkü zaten tam
                # saat bilgisini taşıyor).
                time_field = int(idx.timestamp())
            else:
                # ÖNEMLİ FIX: Günlük/haftalık/aylık mumlarda unix timestamp yerine
                # 'YYYY-MM-DD' string kullanıyoruz. Eskiden idx.timestamp() ile
                # UTC'ye çevrilince, İstanbul saat diliminde gece yarısı olan mum
                # verisi UTC'de bir önceki güne düşüyor ve grafikte mumlar 1 gün
                # geride görünüyordu. Tarih string'i bu sorunu tamamen ortadan kaldırır.
                time_field = idx.strftime("%Y-%m-%d")

            o, h, l, c = float(row["Open"]), float(row["High"]), float(row["Low"]), float(row["Close"])
            candles.append({
                "time": time_field,
                "open": round(o, 2),
                "high": round(h, 2),
                "low": round(l, 2),
                "close": round(c, 2),
            })
            closes.append(c)

        # 5 / 10 günlük SMA kesişimine dayalı basit al-sat sinyalleri
        # (Eskiden hep sondan bir önceki muma sabit "BUY" basılıyordu, anlamsızdı.)
        sma_fast = calculate_sma(closes, 5)
        sma_slow = calculate_sma(closes, 10)
        markers = []
        for i in range(1, len(closes)):
            if None in (sma_fast[i], sma_slow[i], sma_fast[i - 1], sma_slow[i - 1]):
                continue
            prev_diff = sma_fast[i - 1] - sma_slow[i - 1]
            curr_diff = sma_fast[i] - sma_slow[i]
            if prev_diff <= 0 < curr_diff:
                markers.append({"time": candles[i]["time"], "type": "BUY"})
            elif prev_diff >= 0 > curr_diff:
                markers.append({"time": candles[i]["time"], "type": "SELL"})

        live_price = get_live_price(stock, fallback=candles[-1]["close"])
        change_pct = get_daily_change_pct(stock, live_price)

        kap_news = KAP_DATABASE.get(clean_ticker, [
            {"title": f"{clean_ticker} - Özel Durum Açıklaması", "date": "Bugün",
             "body": "Şirket ile ilgili yeni bir KAP bildirimi bulunmamaktadır."}
        ])

        return {
            "ticker": clean_ticker,
            "interval": clean_interval,
            "price": f"{live_price} TL",
            "change_pct": change_pct,
            "candles": candles,
            "markers": markers,
            "kap": kap_news,
        }

    try:
        return get_cached_or_fetch(cache_key, fetch)
    except Exception as e:
        print("Backend Hatası:", e)
        return {"error": f"Sunucu hatası: {str(e)}"}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
