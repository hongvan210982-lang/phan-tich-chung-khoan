"""Công cụ phân tích & đánh giá cổ phiếu.

Chạy: streamlit run app.py
"""

from __future__ import annotations

from datetime import date

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from stock_tool import data_fetcher, data_io, git_sync, indicators, metrics, scoring

# ---- Bảng màu (theo hệ màu chuẩn hoá: categorical cố định thứ tự + status) ----
COLOR_UP = "#0ca30c"       # status good — nến tăng
COLOR_DOWN = "#d03b3b"     # status critical — nến giảm
CAT_COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
GRID_COLOR = "rgba(128,128,128,0.2)"

st.set_page_config(page_title="Phân tích chứng khoán", layout="wide")


@st.cache_data(show_spinner=False)
def _load_all_data() -> dict[str, pd.DataFrame]:
    return data_io.load_all()


def get_data() -> dict[str, pd.DataFrame]:
    if "data" not in st.session_state:
        st.session_state.data = _load_all_data()
    return st.session_state.data


def refresh_data():
    _load_all_data.clear()
    st.session_state.data = _load_all_data()


def _sync_and_notify(commit_message: str) -> None:
    result = git_sync.sync_data_dir(commit_message)
    if result == "skip":
        return
    if result.startswith("Đã đồng bộ") or result.startswith("Không có thay đổi"):
        st.toast(result, icon="✅")
    else:
        st.warning(f"Đồng bộ GitHub: {result}")


def filter_by_date(df: pd.DataFrame, start: date, end: date) -> pd.DataFrame:
    mask = (df["Date"].dt.date >= start) & (df["Date"].dt.date <= end)
    return df.loc[mask].reset_index(drop=True)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

data = get_data()

st.sidebar.header("Dữ liệu")

if not data:
    st.sidebar.warning("Chưa có dữ liệu nào trong thư mục 'Dữ liệu thô'.")
else:
    min_date = min(df["Date"].min().date() for df in data.values())
    max_date = max(df["Date"].max().date() for df in data.values())

    all_tickers = sorted(data.keys())
    selected_tickers = st.sidebar.multiselect(
        "Chọn mã theo dõi", all_tickers, default=all_tickers[: min(5, len(all_tickers))]
    )

    date_range = st.sidebar.date_input(
        "Khoảng thời gian", value=(min_date, max_date), min_value=min_date, max_value=max_date
    )
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date, end_date = min_date, max_date

with st.sidebar.expander("Cập nhật / thêm mã mới", expanded=False):
    st.caption("Lấy dữ liệu mới nhất qua vnstock cho các mã đã có.")
    if st.button("Cập nhật dữ liệu mới nhất", use_container_width=True):
        progress = st.progress(0.0, text="Đang cập nhật...")
        errors = []
        tickers_now = list(data.keys())
        for i, t in enumerate(tickers_now):
            try:
                updated = data_fetcher.fetch_update(data[t], t)
                data_io.save_ticker_data(t, updated)
            except data_fetcher.FetchError as e:
                errors.append(str(e))
            progress.progress((i + 1) / max(len(tickers_now), 1), text=f"Đã cập nhật {t}")
        refresh_data()
        progress.empty()
        if errors:
            st.error("Một số mã lỗi:\n" + "\n".join(errors))
        else:
            st.success("Đã cập nhật dữ liệu mới nhất cho tất cả các mã.")
        _sync_and_notify(f"Cập nhật dữ liệu tự động ({date.today().isoformat()})")
        st.rerun()

    st.divider()
    st.caption("Thêm một mã cổ phiếu mới vào danh sách theo dõi.")
    new_ticker = st.text_input("Mã cổ phiếu (ví dụ: HDB)").strip().upper()
    new_start = st.date_input("Lấy dữ liệu từ ngày", value=date(2021, 1, 1), key="new_ticker_start")
    if st.button("Thêm mã", use_container_width=True):
        if not new_ticker:
            st.warning("Vui lòng nhập mã cổ phiếu.")
        elif new_ticker in data:
            st.warning(f"Mã {new_ticker} đã có trong danh sách.")
        else:
            try:
                with st.spinner(f"Đang tải dữ liệu cho {new_ticker}..."):
                    df_new = data_fetcher.fetch_history(new_ticker, start_date=new_start.isoformat())
                    data_io.save_ticker_data(new_ticker, df_new)
                refresh_data()
                st.success(f"Đã thêm mã {new_ticker} ({len(df_new)} phiên giao dịch).")
                _sync_and_notify(f"Thêm mã {new_ticker}")
                st.rerun()
            except data_fetcher.FetchError as e:
                st.error(str(e))

st.sidebar.caption(
    "Nguồn dữ liệu tự động: vnstock (thư viện cộng đồng, không đảm bảo uptime). "
    "Bạn cũng có thể tự chép file CSV cùng định dạng (Date, Open, High, Low, Close, Volume) "
    "vào thư mục 'Dữ liệu thô'."
)

# ---------------------------------------------------------------------------
# Nội dung chính
# ---------------------------------------------------------------------------

st.title("Phân tích & đánh giá cổ phiếu")

if not data:
    st.info("Thêm mã cổ phiếu ở thanh bên trái để bắt đầu.")
    st.stop()

if not selected_tickers:
    st.info("Chọn ít nhất một mã ở thanh bên trái.")
    st.stop()

filtered = {t: filter_by_date(data[t], start_date, end_date) for t in selected_tickers}
filtered = {t: df for t, df in filtered.items() if len(df) > 1}
indicator_data = {t: indicators.add_all_indicators(df) for t, df in filtered.items()}

tab_chart, tab_perf, tab_rank = st.tabs(["📈 Biểu đồ kỹ thuật", "📊 Hiệu suất & Rủi ro", "🏆 Xếp hạng so sánh"])

# ---- Tab 1: Biểu đồ kỹ thuật ----
with tab_chart:
    ticker = st.selectbox("Chọn mã để xem chi tiết", selected_tickers, key="chart_ticker")
    df = indicator_data.get(ticker)
    if df is None or df.empty:
        st.warning("Không có dữ liệu trong khoảng thời gian đã chọn.")
    else:
        sig = indicators.latest_signal(df)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Giá đóng cửa gần nhất", f"{sig['Giá đóng cửa']:,.0f}")
        c2.metric("Xu hướng", sig["Xu hướng"])
        c3.metric("RSI(14)", f"{sig['RSI(14)']:.1f}" if pd.notna(sig["RSI(14)"]) else "—", sig["RSI nhận định"])
        c4.metric("MACD", sig["MACD"], help="Tích cực = đường MACD đang trên đường Signal; Tiêu cực = đang dưới.")

        fig = make_subplots(
            rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.03,
            row_heights=[0.5, 0.15, 0.17, 0.18],
            subplot_titles=("Giá & đường trung bình động", "Khối lượng", "RSI(14)", "MACD"),
        )

        fig.add_trace(go.Candlestick(
            x=df["Date"], open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
            name="Giá", increasing_line_color=COLOR_UP, decreasing_line_color=COLOR_DOWN,
            showlegend=False,
        ), row=1, col=1)
        fig.add_trace(go.Scatter(x=df["Date"], y=df["BB_upper"], name="BB trên", line=dict(color=CAT_COLORS[0], width=1, dash="dot"), opacity=0.5), row=1, col=1)
        fig.add_trace(go.Scatter(x=df["Date"], y=df["BB_lower"], name="BB dưới", line=dict(color=CAT_COLORS[0], width=1, dash="dot"), opacity=0.5, fill="tonexty", fillcolor="rgba(42,120,214,0.06)"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df["Date"], y=df["SMA20"], name="SMA20", line=dict(color=CAT_COLORS[0], width=1.5)), row=1, col=1)
        fig.add_trace(go.Scatter(x=df["Date"], y=df["SMA50"], name="SMA50", line=dict(color=CAT_COLORS[1], width=1.5)), row=1, col=1)
        fig.add_trace(go.Scatter(x=df["Date"], y=df["SMA200"], name="SMA200", line=dict(color=CAT_COLORS[6], width=1.5)), row=1, col=1)

        vol_colors = [COLOR_UP if c >= o else COLOR_DOWN for o, c in zip(df["Open"], df["Close"])]
        fig.add_trace(go.Bar(x=df["Date"], y=df["Volume"], name="Khối lượng", marker_color=vol_colors, opacity=0.5, showlegend=False), row=2, col=1)

        fig.add_trace(go.Scatter(x=df["Date"], y=df["RSI14"], name="RSI14", line=dict(color=CAT_COLORS[0], width=1.5), showlegend=False), row=3, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color=COLOR_DOWN, opacity=0.5, row=3, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color=COLOR_UP, opacity=0.5, row=3, col=1)

        macd_colors = [COLOR_UP if v >= 0 else COLOR_DOWN for v in df["MACD_hist"].fillna(0)]
        fig.add_trace(go.Bar(x=df["Date"], y=df["MACD_hist"], name="Histogram", marker_color=macd_colors, opacity=0.4, showlegend=False), row=4, col=1)
        fig.add_trace(go.Scatter(x=df["Date"], y=df["MACD"], name="MACD", line=dict(color=CAT_COLORS[0], width=1.5)), row=4, col=1)
        fig.add_trace(go.Scatter(x=df["Date"], y=df["MACD_signal"], name="Signal", line=dict(color=CAT_COLORS[1], width=1.5)), row=4, col=1)

        fig.update_layout(
            height=900, template="plotly_white",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
            margin=dict(t=60, b=20), hovermode="x unified",
            xaxis_rangeslider_visible=False,
        )
        fig.update_xaxes(gridcolor=GRID_COLOR, showgrid=True)
        fig.update_yaxes(gridcolor=GRID_COLOR, showgrid=True)

        st.plotly_chart(fig, use_container_width=True)
        st.caption("Tín hiệu kỹ thuật ở trên là quy tắc heuristic tham khảo, không phải khuyến nghị đầu tư.")

# ---- Tab 2: Hiệu suất & Rủi ro ----
with tab_perf:
    st.subheader("So sánh hiệu suất (giá chuẩn hoá về mốc 100)")
    fig2 = go.Figure()
    for i, t in enumerate(selected_tickers):
        df = filtered.get(t)
        if df is None or df.empty:
            continue
        norm = metrics.normalized_price_series(df)
        fig2.add_trace(go.Scatter(x=df["Date"], y=norm, name=t, line=dict(color=CAT_COLORS[i % len(CAT_COLORS)], width=2)))
    fig2.update_layout(
        height=420, template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(t=40, b=20), hovermode="x unified",
        yaxis_title="Chỉ số (mốc 100 = đầu kỳ)",
    )
    fig2.update_xaxes(gridcolor=GRID_COLOR)
    fig2.update_yaxes(gridcolor=GRID_COLOR)
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Bảng thống kê hiệu suất & rủi ro")
    rf = st.number_input("Lãi suất phi rủi ro giả định (%/năm, dùng để tính Sharpe)", value=0.0, step=0.5) / 100
    rows = {}
    for t in selected_tickers:
        df = filtered.get(t)
        if df is None or df.empty:
            continue
        rows[t] = metrics.summarize(df, risk_free_annual=rf)
    if rows:
        perf_df = pd.DataFrame(rows).T
        st.dataframe(perf_df.style.format("{:.2f}", na_rep="—"), use_container_width=True)
    else:
        st.info("Không có dữ liệu để thống kê.")

# ---- Tab 3: Xếp hạng so sánh ----
with tab_rank:
    st.subheader("Xếp hạng tổng hợp giữa các mã đang chọn")
    st.caption("Điểm 0-100 theo phần trăm xếp hạng tương đối giữa các mã đang chọn, không phải điểm tuyệt đối.")

    weight_cols = st.columns(4)
    weights = {}
    default_items = list(scoring.DEFAULT_WEIGHTS.items())
    for col, (label, default_w) in zip(weight_cols, default_items):
        weights[label] = col.slider(label, 0.0, 1.0, float(default_w), 0.05)

    if len(indicator_data) < 2:
        st.info("Chọn ít nhất 2 mã để so sánh xếp hạng.")
    else:
        ranking = scoring.build_ranking(indicator_data, weights=weights)
        display_cols = ["Điểm tổng hợp"] + list(scoring.DEFAULT_WEIGHTS.keys()) + ["RSI(14)", "Giá đóng cửa"]
        st.dataframe(
            ranking[display_cols].style.format("{:.2f}", na_rep="—").background_gradient(
                subset=["Điểm tổng hợp"], cmap="Greens"
            ),
            use_container_width=True,
        )
        top = ranking.index[0]
        st.success(f"Mã có điểm tổng hợp cao nhất trong danh sách đang chọn: **{top}**")
