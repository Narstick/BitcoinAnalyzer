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

def breakout_probability(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]

    price = last["close"]

    ma7 = last["ma7"]
    ma25 = last["ma25"]
    ma99 = last["ma99"]

    # 🔊 volumen
    vol_mean = df["volume"].rolling(20).mean().iloc[-1]
    vol_ratio = last["volume"] / vol_mean

    # 📏 expansión del movimiento
    expansion = abs(ma7 - ma25) / ma99 * 100

    # =========================
    # 🧠 SCORE INICIAL
    # =========================
    score = 0

    # 🔊 1. volumen
    if vol_ratio > 1.5:
        score += 30
    elif vol_ratio > 1.2:
        score += 15
    else:
        score -= 10

    # 📈 2. estructura de tendencia
    if ma7 > ma25 > ma99:
        score += 25
    elif price > ma99:
        score += 10
    else:
        score -= 20

    # 📏 3. expansión real
    if expansion > 3:
        score += 20
    elif expansion > 1.5:
        score += 10
    else:
        score -= 10

    # 🔁 4. confirmación (precio sosteniéndose arriba)
    if price > ma25 and price > ma99:
        score += 25
    else:
        score -= 15

    # =========================
    # 🎯 LIMITES
    # =========================
    score = max(0, min(100, score))

    # =========================
    # RESULTADO
    # =========================
    print("----- BREAKOUT ANALYSIS -----")
    print(f"Score de breakout real: {score}%")

    if score >= 70:
        print("🔥 BREAKOUT REAL PROBABLE")
    elif score >= 45:
        print("⚠️ MOVIMIENTO DUDOSO (posible fakeout)")
    else:
        print("❌ ALTO RIESGO DE FAKEOUT")

    return score

def detect_liquidity_grab(df, lookback=25):
    last = df.iloc[-1]

    price = last["close"]
    volume = last["volume"]

    # 📊 máximos y mínimos recientes
    recent_high = df["high"].iloc[-lookback:-1].max()
    recent_low = df["low"].iloc[-lookback:-1].min()

    # 🔊 volumen promedio
    vol_mean = df["volume"].rolling(20).mean().iloc[-1]
    vol_ratio = volume / vol_mean

    # =========================
    # 🧠 condiciones
    # =========================

    # 🔴 barrida de máximos (fake breakout arriba)
    sweep_high = last["high"] > recent_high and price < recent_high

    # 🔵 barrida de mínimos (fake breakdown abajo)
    sweep_low = last["low"] < recent_low and price > recent_low

    # 🔊 participación (smart money suele usar volumen alto)
    active_move = vol_ratio > 1.2

    print("----- LIQUIDITY GRAB CHECK -----")

    if sweep_high and active_move:
        print("⚠️ LIQUIDITY GRAB ARRIBA (fake breakout)")
        return "FAKE_BREAKOUT_UP"

    elif sweep_low and active_move:
        print("⚠️ LIQUIDITY GRAB ABAJO (fake breakdown)")
        return "FAKE_BREAKDOWN"

    else:
        print("✅ No hay evidencia clara de liquidity grab")
        return "NO_LIQUIDITY_GRAB"

def detect_resistances(df, lookback=50, tolerance=0.3):
    highs = df["high"]

    levels = []

    # =========================
    # 1. encontrar máximos locales
    # =========================
    for i in range(5, len(df) - 5):
        window = highs[i-5:i+5]
        current = highs.iloc[i]

        if current == window.max():
            levels.append(current)

    # =========================
    # 2. agrupar niveles cercanos
    # =========================
    grouped = []

    for level in levels:
        found = False

        for g in grouped:
            if abs(level - g["price"]) / g["price"] * 100 < tolerance:
                g["touches"] += 1
                found = True
                break

        if not found:
            grouped.append({"price": level, "touches": 1})

    # =========================
    # 3. calcular fuerza
    # =========================
    for g in grouped:
        g["strength"] = g["touches"] * 10  # simple score

    # ordenar por fuerza
    grouped = sorted(grouped, key=lambda x: x["strength"], reverse=True)

    return grouped

def analyze(df):
    prev = df.iloc[-2]
    last = df.iloc[-1]

    print("----- Datos de análisis -----")
    print(f"Precio actual: {last['close']}")
    print(f"ma99: {last['ma99']}")
    print(f"ma25: {last['ma25']}")
    print(f"ma7: {last['ma7']}")
    print(f"RSI: {last['rsi']:.2f}")

    # =========================
    # 📊 DISTANCIA PRECIO vs MA
    # =========================
    price = last["close"]
    ma7 = last["ma7"]
    ma25 = last["ma25"]
    ma99 = last["ma99"]

    dist_price_ma7 = abs(ma7 - price) / ma7 * 100
    dist_price_ma25 = abs(ma25 - price) / ma25 * 100
    dist_price_ma99 = abs(ma99 - price) / ma99 * 100

    print("----- DISTANCIA MA vs PRECIO -----")
    print(f"MA7:  {dist_price_ma7:.2f}%")
    print(f"MA25: {dist_price_ma25:.2f}%")
    print(f"MA99: {dist_price_ma99:.2f}%")

    # =========================
    # 📊 VOLUMEN
    # =========================
    volume = last["volume"]
    vol_mean = df["volume"].rolling(20).mean().iloc[-1]
    vol_ratio = volume / vol_mean

    print("----- VOLUMEN -----")
    print(f"Vol ratio: {vol_ratio:.2f}")

    # =========================
    # 🧠 ESTADO DE TENDENCIA
    # =========================
    bullish_structure = ma7 > ma25 > ma99
    bearish_structure = ma7 < ma25 < ma99

    if bullish_structure:
        trend_state = "🟢 Tendencia alcista fuerte"
    elif bearish_structure:
        trend_state = "🔴 Tendencia bajista fuerte"
    else:
        trend_state = "🟡 Mercado sin estructura clara"

    print("----- TENDENCIA -----")
    print(trend_state)

    # =========================
    # ⚠️ COMPRESIÓN / EXPANSIÓN
    # =========================
    spread = abs(ma7 - ma99) / ma99 * 100

    if spread < 2:
        market_state = "⚠️ Mercado comprimido (posible breakout)"
    elif spread > 6:
        market_state = "🔥 Mercado en expansión"
    else:
        market_state = "📊 Mercado normal"

    print("----- ESTADO DE MERCADO -----")
    print(market_state)

    # =========================
    # 🔥 SOBREEXTENSIÓN PRECIO
    # =========================
    overextended = dist_price_ma99 > 5

    if overextended:
        print("⚠️ Precio muy alejado de MA99 (posible corrección)")

    # =========================
    # 📈 CRUCE MA
    # =========================
    if prev["ma7"] < prev["ma25"] and last["ma7"] > last["ma25"]:
        print("🔥 Cruce alcista MA7 > MA25")

    # =========================
    # 📊 RSI
    # =========================
    if last["rsi"] > 70:
        print("⚠️ Sobrecompra")

    elif last["rsi"] < 30:
        print("⚠️ Sobreventa")

      # =========================
    # 🧠 RESISTENCIAS FUERTES
    # =========================
    resistances = detect_resistances(df)
    strong_levels = [r for r in resistances if r["strength"] >= 20]

    print("----- RESISTENCIAS FUERTES -----")
    for r in strong_levels:
        print(f"{r['price']} | fuerza: {r['strength']} | toques: {r['touches']}")

    # =========================
    # 🚨 DETECCIÓN DE CONFLUENCIA
    # =========================

    price = last["close"]
    near_resistance = False
    for r in strong_levels:
        if abs(price - r["price"]) / price * 100 < 1.0:
            near_resistance = True
            break
    breakout_score = breakout_probability(df)
    liquidity = detect_liquidity_grab(df)

    print("----- DECISIÓN FINAL -----")
    # =========================
    # 🧠 LÓGICA FINAL (MEJORADA)
    # =========================

    if bullish_structure and vol_ratio > 1.2 and last["rsi"] < 70:
        print("🟢 POSIBLE COMPRA (tendencia + volumen + no sobrecompra)")
    elif bearish_structure:
        print("🔴 EVITAR COMPRAS (tendencia bajista)")
    elif spread < 2:
        print("⚠️ ESPERAR (mercado comprimido)")
    else:
        print("📊 SIN SEÑAL CLARA")

    if liquidity != "NO_LIQUIDITY_GRAB":
        print("🚫 NO OPERAR → manipulación detectada (liquidity grab)")
    elif breakout_score >= 70 and not near_resistance:
        print("🟢 BREAKOUT REAL PROBABLE → posible entrada")
    elif near_resistance and vol_ratio < 1.2:
        print("⚠️ EN RESISTENCIA SIN FUERZA → posible rechazo")
    elif spread < 2:
        print("⏳ MERCADO COMPRIMIDO → esperar breakout")
    else:
        print("📊 SIN EDGE CLARO → no operar")

def candle_size(df):
    df["candle_size"] = abs(df["close"] - df["open"])
    return df

def candle_direction(df):
    df["bullish"] = df["close"] > df["open"]
    return df

def candle_wicks(df):
    df["upper_wick"] = df["high"] - df[["open", "close"]].max(axis=1)
    df["lower_wick"] = df[["open", "close"]].min(axis=1) - df["low"]
    return df

def candle_strength(df):
    df["strength"] = df["candle_size"] / (df["high"] - df["low"])
    return df

def detect_engulfing(df):
    prev = df.iloc[-2]
    last = df.iloc[-1]

    # Bullish engulfing
    bullish = (
        prev["close"] < prev["open"] and
        last["close"] > last["open"] and
        last["close"] > prev["open"] and
        last["open"] < prev["close"]
    )

    # Bearish engulfing
    bearish = (
        prev["close"] > prev["open"] and
        last["close"] < last["open"] and
        last["open"] > prev["close"] and
        last["close"] < prev["open"]
    )

    if bullish:
        print("🟢 Bullish Engulfing (posible subida)")

    elif bearish:
        print("🔴 Bearish Engulfing (posible bajada)")

    else:
        print("📊 No engulfing")

def analyze_last_candle(df):
    last = df.iloc[-1]

    body = abs(last["close"] - last["open"])
    upper_wick = last["high"] - max(last["close"], last["open"])
    lower_wick = min(last["close"], last["open"]) - last["low"]
    range_ = last["high"] - last["low"]

    print("----- VELA ACTUAL -----")
    print(f"Cuerpo: {body:.2f}")
    print(f"Mecha superior: {upper_wick:.2f}")
    print(f"Mecha inferior: {lower_wick:.2f}")

    # 🧠 clasificación simple
    if body / range_ > 0.6:
        print("🔥 VELA FUERTE (impulso real)")

    elif upper_wick > body * 2:
        print("⚠️ RECHAZO ARRIBA (posible venta)")

    elif lower_wick > body * 2:
        print("⚠️ RECHAZO ABAJO (posible compra)")

    else:
        print("📊 VELA NEUTRAL")

    detect_engulfing(df)

# Ejecutar
df = get_data()
df = get_ma_data(df)
df = get_rsi_data(df)
analyze(df)
df = candle_size(df)
df = candle_direction(df)
df = candle_wicks(df)
df = candle_strength(df)
analyze_last_candle(df)