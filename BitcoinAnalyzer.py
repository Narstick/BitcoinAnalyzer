import ccxt
import pandas as pd
import ta

exchange = ccxt.binance()

def get_data(symbol="BTC/USDT", timeframe="1h", limit=200):
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    
    df = pd.DataFrame(ohlcv, columns=[
        "timestamp", "open", "high", "low", "close", "volume"
    ])
    
    df["close"] = df["close"].astype(float)
    return df

def add_indicators(df):
    df["ma50"] = df["close"].rolling(50).mean()
    df["ma100"] = df["close"].rolling(100).mean()
    df["ma200"] = df["close"].rolling(200).mean()
    df["rsi"] = ta.momentum.RSIIndicator(df["close"], window=14).rsi()
    return df

def clean_data(df):
    df = df.dropna()
    return df

def analyze(df):
    last = df.iloc[-1]
    tendencia_fuerte = last["ma50"] > last["ma100"] > last["ma200"]
    tendencia_debil = last["ma50"] < last["ma100"] < last["ma200"]
    rsi = last["rsi"]

    print("----- Datos de análisis -----")
    print(f"Precio actual: {last['close']}")
    print(f"MA200: {last['ma200']}")
    print(f"MA100: {last['ma100']}")
    print(f"MA50: {last['ma50']}")
    print(f"RSI: {rsi:.2f}")

    print("\n----- Señal -----")
    if tendencia_fuerte and 40 < rsi < 60:
        print("🔥 Posible compra (tendencia fuerte + RSI sano)")
    elif tendencia_debil:
        print("🔻 Tendencia bajista, evitar compras")
    else:
        print("⏳ Mercado sin claridad")

# Ejecutar
df = get_data()
df = add_indicators(df)
df = clean_data(df)
analyze(df)