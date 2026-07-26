"""Thống kê hiệu suất & rủi ro dựa trên giá đóng cửa."""

from __future__ import annotations

import numpy as np
import pandas as pd

PERIOD_DAYS = {
    "1 tháng": 21,
    "3 tháng": 63,
    "6 tháng": 126,
    "1 năm": 252,
    "3 năm": 756,
}


def period_return_pct(df: pd.DataFrame, trading_days: int) -> float | None:
    if len(df) <= trading_days:
        return None
    p0 = df["Close"].iloc[-trading_days - 1]
    p1 = df["Close"].iloc[-1]
    if p0 == 0:
        return None
    return (p1 / p0 - 1) * 100


def ytd_return_pct(df: pd.DataFrame) -> float | None:
    last_date = pd.to_datetime(df["Date"].iloc[-1])
    year_start = pd.Timestamp(year=last_date.year, month=1, day=1)
    prior = df[pd.to_datetime(df["Date"]) < year_start]
    if prior.empty:
        return None
    p0 = prior["Close"].iloc[-1]
    p1 = df["Close"].iloc[-1]
    if p0 == 0:
        return None
    return (p1 / p0 - 1) * 100


def annualized_volatility_pct(df: pd.DataFrame, window: int | None = None) -> float | None:
    rets = df["Close"].pct_change().dropna()
    if window:
        rets = rets.tail(window)
    if len(rets) < 2:
        return None
    return rets.std() * np.sqrt(252) * 100


def max_drawdown_pct(df: pd.DataFrame) -> float | None:
    rets = df["Close"].pct_change().fillna(0)
    cum = (1 + rets).cumprod()
    peak = cum.cummax()
    dd = cum / peak - 1
    return dd.min() * 100


def sharpe_ratio(df: pd.DataFrame, risk_free_annual: float = 0.0) -> float | None:
    rets = df["Close"].pct_change().dropna()
    if len(rets) < 2 or rets.std() == 0:
        return None
    excess = rets - risk_free_annual / 252
    return (excess.mean() / rets.std()) * np.sqrt(252)


def summarize(df: pd.DataFrame, risk_free_annual: float = 0.0) -> dict:
    row: dict[str, float | None] = {}
    for label, days in PERIOD_DAYS.items():
        row[f"Lợi nhuận {label} (%)"] = period_return_pct(df, days)
    row["Lợi nhuận từ đầu năm (%)"] = ytd_return_pct(df)
    row["Biến động năm hoá (%)"] = annualized_volatility_pct(df)
    row["Sụt giảm tối đa (%)"] = max_drawdown_pct(df)
    row["Sharpe ratio"] = sharpe_ratio(df, risk_free_annual)
    return row


def normalized_price_series(df: pd.DataFrame, base: float = 100.0) -> pd.Series:
    return df["Close"] / df["Close"].iloc[0] * base
