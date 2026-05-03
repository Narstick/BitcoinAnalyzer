import ccxt
import pandas as pd
import ta
import numpy as np

exchange = ccxt.binance()

def get_data(symbol="BTC/USDT", timeframe="4h", limit=200):
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)

    df = pd.DataFrame(ohlcv, columns=[
        "timestamp", "open", "high", "low", "close", "volume"
    ])

    df["close"] = df["close"].astype(float)
    df["volume"] = df["volume"].astype(float)

    return df

def get_ma_data(df):
    df["ma7"] = df["close"].rolling(7).mean()
    df["ma25"] = df["close"].rolling(25).mean()
    df["ma99"] = df["close"].rolling(99).mean()
    return df

def get_rsi_data(df):
    df["rsi"] = ta.momentum.RSIIndicator(df["close"], window=12).rsi()
    return df 

def analyze(df):
    prev = df.iloc[-2]
    last = df.iloc[-1]
    print("----- Datos de análisis -----")
    print(f"Precio actual: {last['close']}")
    print(f"ma99: {last['ma99']}")
    print(f"ma25: {last['ma25']}")
    print(f"ma7: {last['ma7']}")
    print(f"RSI: {last['rsi']:.2f}")

    # === Analisis distancia MA ===
    price = last["close"]
    ma7 = last["ma7"]
    ma25 = last["ma25"]
    ma99 = last["ma99"]
    dist_price_ma7 = (ma7-price) / ma7 * 100
    dist_price_ma25 = (ma25-price) / ma25 * 100
    dist_price_ma99 = (ma99-price) / ma99 * 100
    print("----- DISTANCIA MA vs PRECIO -----")
    print(f"Precio: {price}")
    print(f"MA7:  {dist_price_ma7:.2f}%")
    print(f"MA25: {dist_price_ma25:.2f}%")
    print(f"MA99: {dist_price_ma99:.2f}%")

    # === Analisis volúmen ===
    volume = last["volume"]
    vol_mean = df["volume"].rolling(20).mean().iloc[-1]
    vol_ratio = volume / vol_mean
    print("----- RATIO DE VOLUMEN -----")
    print(f"Vol. Ratio: {vol_ratio}")


    if vol_ratio > 1.5:
        print("🔥 Volumen alto → movimiento fuerte confirmado")

    elif vol_ratio < 0.8:
        print("⚠️ Volumen bajo → movimiento débil")

    else:
        print("📊 Volumen normal")


    if prev["ma7"] < prev["ma25"] and last["ma7"] > last["ma25"]:
        print("🔥 Cruce alcista MA7 > MA25 (short term)")
    elif last["close"] > last["ma99"]:
        print("📈 Tendencia alcista general")

    elif last["rsi"] > 70:
        print("⚠️ Sobrecompra")

    elif last["rsi"] < 30:
        print("⚠️ Sobreventa")
    else:
        print("📊 Sin señal clara")
# Ejecutar
df = get_data()
df = get_ma_data(df)
df = get_rsi_data(df)
analyze(df)