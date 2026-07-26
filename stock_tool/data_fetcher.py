"""Tải dữ liệu giá cổ phiếu Việt Nam qua thư viện vnstock.

Toàn bộ phần tích hợp với vnstock được gói gọn trong file này. Nếu sau này
vnstock đổi API (hoặc bạn nâng cấp Python lên >=3.10 và dùng vnstock 3/4.x),
chỉ cần sửa lại hàm fetch_history() ở đây, các phần khác của công cụ không
cần thay đổi.
"""

from __future__ import annotations

import warnings
from datetime import date, timedelta

import pandas as pd

warnings.filterwarnings("ignore")


class FetchError(Exception):
    pass


def fetch_history(ticker: str, start_date: str, end_date: str | None = None) -> pd.DataFrame:
    """Lấy dữ liệu OHLCV lịch sử cho một mã, trả về DataFrame với cột
    Date, Open, High, Low, Close, Volume."""
    end_date = end_date or date.today().isoformat()
    try:
        from vnstock import stock_historical_data
    except ImportError as e:
        raise FetchError(
            "Chưa cài thư viện vnstock. Chạy: pip install -r requirements.txt"
        ) from e

    try:
        df = stock_historical_data(
            symbol=ticker.upper(),
            start_date=start_date,
            end_date=end_date,
            resolution="1D",
            type="stock",
        )
    except Exception as e:  # vnstock ném nhiều loại lỗi khác nhau khi mã sai/hết hạn API
        raise FetchError(f"Không tải được dữ liệu cho mã {ticker}: {e}") from e

    if df is None or len(df) == 0:
        raise FetchError(f"Không có dữ liệu trả về cho mã {ticker} trong khoảng {start_date} - {end_date}")

    df = df.rename(
        columns={
            "time": "Date",
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "volume": "Volume",
        }
    )
    df["Date"] = pd.to_datetime(df["Date"]).dt.normalize()
    df = df.sort_values("Date").reset_index(drop=True)
    return df[["Date", "Open", "High", "Low", "Close", "Volume"]]


def fetch_update(existing_df: pd.DataFrame, ticker: str) -> pd.DataFrame:
    """Lấy các phiên giao dịch mới hơn ngày cuối cùng đã có, gộp vào dữ liệu cũ."""
    last_date = pd.to_datetime(existing_df["Date"]).max().date()
    start = (last_date + timedelta(days=1)).isoformat()
    today = date.today().isoformat()
    if start > today:
        return existing_df
    new_rows = fetch_history(ticker, start_date=start, end_date=today)
    if new_rows.empty:
        return existing_df
    combined = pd.concat([existing_df, new_rows], ignore_index=True)
    combined = combined.sort_values("Date").drop_duplicates("Date", keep="last").reset_index(drop=True)
    return combined
