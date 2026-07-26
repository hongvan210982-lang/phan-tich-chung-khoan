# Tài liệu bàn giao — Công cụ phân tích & đánh giá chứng khoán

Ngày cập nhật: 2026-07-27

## 1. Mục tiêu dự án

Dashboard Streamlit phân tích kỹ thuật, hiệu suất/rủi ro và xếp hạng so sánh
nhiều mã cổ phiếu, dựa trên dữ liệu OHLCV (Open/High/Low/Close/Volume) theo
ngày. Thiết kế để dễ mở rộng: thêm mã mới hoặc đổi khoảng thời gian mà không
cần sửa code.

## 2. Trạng thái hiện tại

- [x] Code hoàn chỉnh, đã test chạy local (`streamlit run app.py`) — không lỗi,
      biểu đồ/bảng render đúng.
- [x] Đã khởi tạo git repo local, commit đầu tiên: `7ba90c1`.
- [x] Đã tạo GitHub repo và push code: **https://github.com/hongvan210982-lang/phan-tich-chung-khoan**
- [x] Repo hiện đang **public** (đổi từ private vì Streamlit Community Cloud
      không cấp được quyền đọc repo private qua trình duyệt — xem mục 6).
- [ ] **Deploy lên Streamlit Community Cloud — đang thao tác dở, chưa xác nhận
      thành công.** Bước cuối: vào share.streamlit.io → Deploy an app → nhập
      `hongvan210982-lang/phan-tich-chung-khoan`, branch `main`, main file
      `app.py`.

## 3. Cấu trúc dự án

```
Dữ liệu thô/              ← dữ liệu giá thô, mỗi mã 1 file CSV (Date,Open,High,Low,Close,Volume)
stock_tool/
  data_io.py               ← đọc/ghi file CSV, nhận diện mã theo tên file
  data_fetcher.py           ← tải dữ liệu mới qua vnstock (toàn bộ phụ thuộc vnstock nằm ở đây)
  indicators.py             ← chỉ báo kỹ thuật: SMA/EMA, RSI, MACD, Bollinger Bands
  metrics.py                 ← hiệu suất theo giai đoạn, biến động, max drawdown, Sharpe
  scoring.py                  ← điểm xếp hạng tổng hợp giữa các mã
app.py                        ← giao diện Streamlit (3 tab: biểu đồ, hiệu suất, xếp hạng)
requirements.txt              ← danh sách thư viện cần cài
README.md                     ← hướng dẫn sử dụng chi tiết (cách chạy, thêm mã, cập nhật)
```

Chi tiết cách dùng từng tính năng: xem `README.md`.

## 4. Dữ liệu hiện có

9 mã: BID, BSR, FPT, HPG, MBB, PVS, SSI, VCB, VNM — khoảng thời gian
2021-01-01 đến 2026-07-24, nguồn gốc do người dùng cung cấp sẵn trong
`Dữ liệu thô/`.

## 5. Quyết định kỹ thuật quan trọng & lý do

- **Streamlit thay vì Vercel**: yêu cầu ban đầu là deploy lên Vercel, nhưng
  Vercel chỉ chạy serverless function ngắn hạn, không hỗ trợ server Python
  chạy liên tục + WebSocket mà Streamlit cần → đổi hướng sang Streamlit
  Community Cloud (miễn phí, chính thức cho Streamlit).
- **vnstock phiên bản Legacy (0.2.9.2.3)** thay vì bản mới (3.x/4.x): máy dùng
  Python 3.9, trong khi vnstock 3.x/4.x yêu cầu Python >= 3.10. Đã ghim cứng
  version trong `requirements.txt`. Đã kiểm chứng dữ liệu tải về khớp với dữ
  liệu thô hiện có (so sánh MBB, FPT). Toàn bộ code gọi vnstock nằm gọn trong
  `stock_tool/data_fetcher.py` để dễ thay khi cần — hướng dẫn nâng cấp ở cuối
  `README.md`.
- **Repo public thay vì private**: xem mục 6.

## 6. Vướng mắc đã gặp khi deploy & cách đã xử lý

Streamlit Community Cloud cần quyền đọc nội dung repo GitHub để deploy. Khi
repo ở chế độ private, nhiều lần thử cấp quyền qua GitHub (đăng nhập lại,
revoke/re-authorize OAuth app "Streamlit") đều không hiệu quả — trang xin
quyền của GitHub không hiện lại (do phiên đăng nhập đã được nhớ), và trang xác
nhận quyền của ứng dụng "Streamlit" trên GitHub chỉ hiển thị scope
**"Access public repositories"**, không có tuỳ chọn cấp quyền private repo.
→ Quyết định (đã hỏi và được xác nhận): **đổi repo sang public** để bỏ qua
vướng mắc này, chấp nhận đánh đổi là code + dữ liệu giá cổ phiếu lịch sử công
khai (không chứa thông tin nhạy cảm, không có secret/API key nào).

Nếu sau này muốn thử lại private + Streamlit Cloud: có thể cần tìm đúng mục
"GitHub App" riêng (không phải OAuth App) trong phần liên kết tài khoản của
Streamlit, khác với OAuth App "Streamlit" đã thấy tại
`github.com/settings/applications`.

## 7. Việc cần làm tiếp theo

1. **[Cần bạn thao tác thủ công trên trình duyệt — không tự động hoá được vì
   cần đăng nhập GitHub OAuth của bạn]** Hoàn tất deploy trên share.streamlit.io:
   vào https://share.streamlit.io → đăng nhập GitHub `hongvan210982-lang` →
   Deploy an app → repo `hongvan210982-lang/phan-tich-chung-khoan`, branch
   `main`, main file `app.py` → Deploy.
2. Sau khi deploy xong, lưu lại URL dạng `https://xxx.streamlit.app` (báo lại
   cho Claude để cập nhật mục này).
3. **[Đã làm]** Tính năng tự động commit + push dữ liệu khi cập nhật trên
   cloud đã được thêm (`stock_tool/git_sync.py`, gọi từ `app.py` sau mỗi lần
   "Thêm mã"/"Cập nhật dữ liệu mới nhất"). Mặc định **tắt** — cần cấu hình
   secret `GITHUB_TOKEN` trên Streamlit Cloud (App settings → Secrets) mới
   kích hoạt. Không có token thì bỏ qua lặng lẽ, không ảnh hưởng chạy local.
   Chi tiết cách tạo token & cấu hình: xem mục "Đồng bộ dữ liệu tự động lên
   GitHub" trong `README.md`.
4. (Tuỳ chọn) Nếu muốn quay lại private repo: cần giải quyết dứt điểm việc cấp
   quyền GitHub App cho Streamlit trước khi đổi visibility lại.

## 8. Thông tin tài khoản/kết nối liên quan

- GitHub account dùng để tạo repo & đăng nhập Streamlit: `hongvan210982-lang`
- GitHub repo: https://github.com/hongvan210982-lang/phan-tich-chung-khoan (public)
- `gh` CLI đã được cài cục bộ tại `~/.local/bin/gh` và đã `gh auth login` trên
  máy này (dùng để push code, có thể dùng lại cho các thao tác GitHub sau
  này).
- Git identity dùng cho commit trên máy này: name `bnhoang27`, email
  `bnhoang27@gmail.com` (cấu hình local cho riêng repo này, không phải global).

## 9. Rủi ro cần theo dõi

- **vnstock Legacy không còn được bảo trì** — có thể ngừng hoạt động bất kỳ
  lúc nào nếu nguồn dữ liệu (SSI/TCBS) đổi API. Dữ liệu cũ trong
  `Dữ liệu thô/` không bị ảnh hưởng, chỉ chức năng "thêm mã/cập nhật" bị lỗi.
- **Không có cơ chế xác thực người dùng** trên app — nếu deploy public, bất kỳ
  ai có link đều dùng được, kể cả bấm nút tải dữ liệu (không nguy hiểm nhưng
  tốn tài nguyên free-tier nếu bị lạm dụng).
- Điểm xếp hạng/tín hiệu kỹ thuật trong app là quy tắc heuristic tham khảo,
  **không phải khuyến nghị đầu tư**.
