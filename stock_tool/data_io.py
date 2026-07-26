"""Đọc/ghi dữ liệu giá cổ phiếu (OHLCV) từ thư mục Dữ liệu thô.

Quy ước tên file: {MÃ}_{ngày bắt đầu}_{ngày kết thúc}.csv, ví dụ FPT_2021-01-01_2026-07-24.csv
Mỗi mã chỉ nên có một file. Khi cập nhật dữ liệu, file cũ sẽ được thay bằng file mới có
tên phản ánh khoảng thời gian mới.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "Dữ liệu thô"

FILENAME_RE = re.compile(r"^([A-Za-z0-9]+)_(\d{4}-\d{2}-\d{2})_(\d{4}-\d{2}-\d{2})\.csv$")

REQUIRED_COLUMNS = ["Date", "Open", "High", "Low", "Close", "Volume"]


def _parse_ticker_from_filename(path: Path) -> str:
    m = FILENAME_RE.match(path.name)
    if m:
        return m.group(1).upper()
    return path.stem.split("_")[0].upper()


def list_ticker_files() -> dict[str, Path]:
    """Trả về map {mã: đường dẫn file}. Nếu một mã có nhiều file, chỉ giữ file có
    ngày kết thúc mới nhất (các file cũ không bị xoá, chỉ bị bỏ qua)."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    best: dict[str, tuple[str, Path]] = {}
    for f in sorted(DATA_DIR.glob("*.csv")):
        ticker = _parse_ticker_from_filename(f)
        m = FILENAME_RE.match(f.name)
        end_key = m.group(3) if m else ""
        if ticker not in best or end_key >= best[ticker][0]:
            best[ticker] = (end_key, f)
    return {t: p for t, (_, p) in best.items()}


def list_tickers() -> list[str]:
    return sorted(list_ticker_files().keys())


def load_ticker_data(ticker: str) -> pd.DataFrame:
    files = list_ticker_files()
    path = files.get(ticker.upper())
    if path is None:
        raise FileNotFoundError(f"Không tìm thấy dữ liệu cho mã {ticker}")
    df = pd.read_csv(path, encoding="utf-8-sig")
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"File {path.name} thiếu cột: {missing}")
    df["Date"] = pd.to_datetime(df["Date"]).dt.normalize()
    df = df.sort_values("Date").drop_duplicates("Date", keep="last").reset_index(drop=True)
    return df[REQUIRED_COLUMNS]


def load_all() -> dict[str, pd.DataFrame]:
    data = {}
    for ticker in list_tickers():
        try:
            data[ticker] = load_ticker_data(ticker)
        except (FileNotFoundError, ValueError):
            continue
    return data


def save_ticker_data(ticker: str, df: pd.DataFrame) -> Path:
    """Ghi dữ liệu ra file chuẩn hoá và xoá các file cũ khác của cùng mã đó."""
    ticker = ticker.upper()
    df = df.sort_values("Date").drop_duplicates("Date", keep="last").reset_index(drop=True)
    start = pd.to_datetime(df["Date"].iloc[0]).date().isoformat()
    end = pd.to_datetime(df["Date"].iloc[-1]).date().isoformat()
    new_path = DATA_DIR / f"{ticker}_{start}_{end}.csv"

    old_files = [p for t, p in list_ticker_files().items() if t == ticker]
    out = df.copy()
    out["Date"] = pd.to_datetime(out["Date"]).dt.strftime("%Y-%m-%d")
    out.to_csv(new_path, index=False)

    for old in old_files:
        if old.resolve() != new_path.resolve():
            old.unlink(missing_ok=True)

    return new_path
