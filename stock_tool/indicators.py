"""Các chỉ báo phân tích kỹ thuật tính từ dữ liệu OHLCV."""

from __future__ import annotations

import numpy as np
import pandas as pd

MA_WINDOWS = (20, 50, 200)
EMA_SPANS = (12, 26)
RSI_PERIOD = 14
MACD_FAST, MACD_SLOW, MACD_SIGNAL = 12, 26, 9
BB_WINDOW, BB_STD = 20, 2


def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    for w in MA_WINDOWS:
        df[f"SMA{w}"] = df["Close"].rolling(w).mean()

    for s in EMA_SPANS:
        df[f"EMA{s}"] = df["Close"].ewm(span=s, adjust=False).mean()

    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / RSI_PERIOD, adjust=False, min_periods=RSI_PERIOD).mean()
    avg_loss = loss.ewm(alpha=1 / RSI_PERIOD, adjust=False, min_periods=RSI_PERIOD).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    df["RSI14"] = 100 - (100 / (1 + rs))
    df["RSI14"] = df["RSI14"].fillna(50)

    ema_fast = df["Close"].ewm(span=MACD_FAST, adjust=False).mean()
    ema_slow = df["Close"].ewm(span=MACD_SLOW, adjust=False).mean()
    df["MACD"] = ema_fast - ema_slow
    df["MACD_signal"] = df["MACD"].ewm(span=MACD_SIGNAL, adjust=False).mean()
    df["MACD_hist"] = df["MACD"] - df["MACD_signal"]

    mid = df["Close"].rolling(BB_WINDOW).mean()
    std = df["Close"].rolling(BB_WINDOW).std()
    df["BB_mid"] = mid
    df["BB_upper"] = mid + BB_STD * std
    df["BB_lower"] = mid - BB_STD * std

    df["Volatility20"] = df["Close"].pct_change().rolling(20).std() * np.sqrt(252) * 100

    return df


def latest_signal(df: pd.DataFrame) -> dict:
    """Tóm tắt tín hiệu kỹ thuật gần nhất. Đây là quy tắc heuristic đơn giản
    để tham khảo, không phải khuyến nghị đầu tư."""
    last = df.iloc[-1]
    close = last["Close"]
    sma50 = last.get("SMA50", np.nan)
    sma200 = last.get("SMA200", np.nan)

    if pd.notna(sma50) and pd.notna(sma200):
        if close > sma50 > sma200:
            trend = "Tăng mạnh"
        elif close > sma200:
            trend = "Tăng"
        elif close < sma50 < sma200:
            trend = "Giảm mạnh"
        else:
            trend = "Giảm / Trung lập"
    else:
        trend = "Chưa đủ dữ liệu"

    rsi = last.get("RSI14", np.nan)
    if pd.isna(rsi):
        rsi_label = "Chưa đủ dữ liệu"
    elif rsi >= 70:
        rsi_label = "Quá mua"
    elif rsi <= 30:
        rsi_label = "Quá bán"
    else:
        rsi_label = "Trung tính"

    macd, macd_sig = last.get("MACD", np.nan), last.get("MACD_signal", np.nan)
    if pd.notna(macd) and pd.notna(macd_sig):
        macd_label = "Tích cực" if macd > macd_sig else "Tiêu cực"
    else:
        macd_label = "Chưa đủ dữ liệu"

    return {
        "Xu hướng": trend,
        "RSI(14)": rsi,
        "RSI nhận định": rsi_label,
        "MACD": macd_label,
        "Giá đóng cửa": close,
    }
