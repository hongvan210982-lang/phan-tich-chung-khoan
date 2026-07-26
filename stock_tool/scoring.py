"""Xếp hạng & so sánh nhiều mã dựa trên các chỉ báo kỹ thuật + hiệu suất/rủi ro.

Đây là một hệ điểm heuristic minh bạch (không phải mô hình định giá), dùng để
so sánh tương đối giữa các mã đang theo dõi. Trọng số có thể điều chỉnh được
trong giao diện.
"""

from __future__ import annotations

import pandas as pd

from stock_tool import metrics

DEFAULT_WEIGHTS = {
    "Đà tăng giá (3T)": 0.30,
    "Xu hướng dài hạn": 0.25,
    "Hiệu suất gần (1T)": 0.20,
    "Rủi ro (biến động & sụt giảm)": 0.25,
}


def _raw_features(ticker: str, df_ind: pd.DataFrame) -> dict:
    last = df_ind.iloc[-1]
    close = last["Close"]
    sma200 = last.get("SMA200")
    trend_gap = ((close / sma200) - 1) * 100 if pd.notna(sma200) and sma200 else None

    vol = metrics.annualized_volatility_pct(df_ind, window=60)
    dd = metrics.max_drawdown_pct(df_ind)
    risk_penalty = None
    if vol is not None and dd is not None:
        risk_penalty = vol - dd  # dd is negative, so -dd adds penalty; smaller is better

    return {
        "Mã": ticker,
        "Đà tăng giá (3T)": metrics.period_return_pct(df_ind, 63),
        "Xu hướng dài hạn": trend_gap,
        "Hiệu suất gần (1T)": metrics.period_return_pct(df_ind, 21),
        "Rủi ro (biến động & sụt giảm)": risk_penalty,
        "RSI(14)": last.get("RSI14"),
        "Giá đóng cửa": close,
    }


def _percentile_score(series: pd.Series, invert: bool = False) -> pd.Series:
    s = series.astype(float)
    if s.notna().sum() < 2:
        return pd.Series([50.0] * len(s), index=s.index)
    ranks = s.rank(pct=True, na_option="keep") * 100
    if invert:
        ranks = 100 - ranks
    return ranks.fillna(50.0)


def build_ranking(data_with_indicators: dict[str, pd.DataFrame], weights: dict | None = None) -> pd.DataFrame:
    weights = weights or DEFAULT_WEIGHTS
    rows = [_raw_features(t, df) for t, df in data_with_indicators.items()]
    raw = pd.DataFrame(rows).set_index("Mã")

    score_cols = ["Đà tăng giá (3T)", "Xu hướng dài hạn", "Hiệu suất gần (1T)", "Rủi ro (biến động & sụt giảm)"]
    scores = pd.DataFrame(index=raw.index)
    for col in score_cols:
        invert = col == "Rủi ro (biến động & sụt giảm)"
        scores[col] = _percentile_score(raw[col], invert=invert)

    total_weight = sum(weights.get(c, 0) for c in score_cols) or 1.0
    composite = sum(scores[c] * weights.get(c, 0) for c in score_cols) / total_weight

    result = raw.copy()
    result["Điểm tổng hợp"] = composite.round(1)
    for col in score_cols:
        result[f"Điểm - {col}"] = scores[col].round(1)

    return result.sort_values("Điểm tổng hợp", ascending=False)
