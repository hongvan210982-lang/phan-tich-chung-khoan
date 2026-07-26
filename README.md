# Công cụ phân tích & đánh giá chứng khoán

Dashboard Streamlit để phân tích kỹ thuật, hiệu suất/rủi ro và xếp hạng so sánh
các mã cổ phiếu, dựa trên dữ liệu OHLCV (Open, High, Low, Close, Volume) theo ngày.

## Cài đặt (chỉ cần làm 1 lần)

```bash
python3 -m pip install -r requirements.txt
```

Lưu ý: `requirements.txt` ghim `vnstock==0.2.9.2.3` vì máy đang dùng Python 3.9
(các phiên bản vnstock mới hơn — 3.x/4.x — yêu cầu Python >= 3.10). Nếu sau này
bạn nâng cấp Python lên 3.10+, xem phần "Nâng cấp nguồn dữ liệu" dưới đây.

## Chạy công cụ

```bash
streamlit run app.py
```

Trình duyệt sẽ tự mở tại `http://localhost:8501`.

## Cấu trúc dự án

```
Dữ liệu thô/              ← dữ liệu giá thô, mỗi mã 1 file CSV (Date,Open,High,Low,Close,Volume)
stock_tool/
  data_io.py               ← đọc/ghi file CSV, nhận diện mã theo tên file
  data_fetcher.py           ← tải dữ liệu mới qua vnstock (toàn bộ phần phụ thuộc vnstock nằm ở đây)
  indicators.py             ← chỉ báo kỹ thuật: SMA/EMA, RSI, MACD, Bollinger Bands
  metrics.py                 ← hiệu suất theo giai đoạn, biến động, sụt giảm tối đa, Sharpe
  scoring.py                  ← điểm xếp hạng tổng hợp giữa các mã
app.py                        ← giao diện Streamlit
```

## Thêm mã cổ phiếu mới

Mở sidebar → mục "Cập nhật / thêm mã mới" → nhập mã (ví dụ `HDB`) và ngày bắt
đầu lấy dữ liệu → bấm **Thêm mã**. Công cụ sẽ tự tải toàn bộ lịch sử giá qua
vnstock và lưu thành file CSV mới trong `Dữ liệu thô/`.

Bạn cũng có thể tự thêm mã bằng cách chép file CSV cùng định dạng cột
(`Date,Open,High,Low,Close,Volume`) vào thư mục `Dữ liệu thô/`, đặt tên theo mẫu
`MÃ_ngày-bắt-đầu_ngày-kết-thúc.csv` — công cụ sẽ tự nhận diện, không cần khởi
động lại.

## Cập nhật dữ liệu mới nhất

Sidebar → "Cập nhật / thêm mã mới" → bấm **Cập nhật dữ liệu mới nhất**. Công cụ
sẽ lấy các phiên giao dịch mới hơn ngày cuối cùng đang có cho từng mã, gộp vào
dữ liệu cũ và ghi đè file.

## Đồng bộ dữ liệu tự động lên GitHub (khi chạy trên Streamlit Cloud)

Filesystem của Streamlit Community Cloud là tạm thời — file CSV lưu qua nút
"Thêm mã" / "Cập nhật dữ liệu mới nhất" sẽ **mất khi app khởi động lại** (app
tự ngủ sau thời gian không dùng) nếu không được đẩy ngược về GitHub.

Để bật đồng bộ tự động: vào app trên share.streamlit.io → **⋮ (menu) → Settings
→ Secrets**, thêm:

```
GITHUB_TOKEN = "ghp_xxxxxxxxxxxxxxxxxxxx"
```

Token tạo tại GitHub → Settings → Developer settings → Personal access tokens,
cần quyền ghi vào repo `hongvan210982-lang/phan-tich-chung-khoan` (fine-grained:
`Contents: Read and write`, hoặc classic scope `repo`). Sau khi thêm secret, mỗi
lần bấm "Thêm mã" hoặc "Cập nhật dữ liệu mới nhất" trên bản cloud, công cụ sẽ tự
`git commit` + `git push` thư mục `Dữ liệu thô/` về nhánh đang deploy.

Chạy local mà không cấu hình `GITHUB_TOKEN` thì tính năng này tự bỏ qua, không
ảnh hưởng gì — bạn vẫn tự `git add`/`git commit`/`git push` như bình thường.
Xem code tại `stock_tool/git_sync.py`.

## Mở rộng khoảng thời gian

Chỉ cần chọn lại khoảng ngày ở thanh trượt ngày trong sidebar — toàn bộ biểu
đồ, bảng hiệu suất và xếp hạng sẽ tự tính lại theo khoảng đã chọn. Muốn có dữ
liệu xa hơn về trước, xoá file CSV của mã đó rồi dùng chức năng "Thêm mã" với
ngày bắt đầu sớm hơn.

## Các phần phân tích

- **Biểu đồ kỹ thuật**: nến giá, SMA20/50/200, Bollinger Bands, khối lượng,
  RSI(14), MACD, kèm tóm tắt xu hướng/tín hiệu hiện tại.
- **Hiệu suất & Rủi ro**: biểu đồ giá chuẩn hoá (mốc 100) để so sánh nhiều mã,
  bảng lợi nhuận theo giai đoạn (1T/3T/6T/1N/3N/YTD), biến động năm hoá, sụt
  giảm tối đa (max drawdown), Sharpe ratio.
- **Xếp hạng so sánh**: điểm tổng hợp 0-100 xếp hạng tương đối các mã đang
  chọn theo 4 tiêu chí (đà tăng giá, xu hướng dài hạn, hiệu suất gần, rủi ro),
  trọng số có thể chỉnh trực tiếp bằng thanh trượt.

Toàn bộ tín hiệu/điểm số là quy tắc heuristic minh bạch để tham khảo và so
sánh tương đối, **không phải khuyến nghị đầu tư**.

## Lưu ý về nguồn dữ liệu tự động

Dữ liệu tự động lấy qua thư viện cộng đồng [`vnstock`](https://github.com/thinh-vu/vnstock)
(bản Legacy 0.2.9.2.3, do giới hạn Python 3.9). Đây không phải API chính thức
nên có thể gián đoạn hoặc đổi định dạng bất ngờ. Nếu chức năng tải dữ liệu báo
lỗi, dữ liệu cũ trong `Dữ liệu thô/` vẫn an toàn — bạn có thể chờ thư viện được
sửa, tự tìm nguồn CSV khác, hoặc nhờ cập nhật lại `data_fetcher.py`.

### Nâng cấp nguồn dữ liệu (khi có Python >= 3.10)

```bash
python3 -m pip install --upgrade "vnstock>=3"
```

Khi đó cần sửa lại hàm `fetch_history()` trong `stock_tool/data_fetcher.py`
theo API mới của vnstock 3.x/4.x (cú pháp `Vnstock().stock(...).quote.history(...)`).
Toàn bộ phần còn lại của công cụ không cần thay đổi.
