# Demo OCR và dịch tài liệu

Web demo một trang: tải PDF/PNG/JPG lên, xem tài liệu gốc cạnh PDF đã dịch và tải PDF bản dịch giữ bố cục. Bản dịch được ghép theo vùng, giữ màu chữ và nền ước lượng từ ảnh. Chữ mới không bị thu nhỏ dưới 7 pt. Nếu thiếu chỗ, vùng được đánh dấu [n] và nội dung đầy đủ nằm trong phần “Bản dịch bổ sung” cuối PDF (ghi rõ trang và mục). Không bảo đảm khôi phục chính xác font hoặc nền có họa tiết.

## Chạy trên Linux (Ubuntu/Debian)

1. Cài Python 3.10+ và Tesseract cùng dữ liệu ngôn ngữ OCR cần dùng. Ví dụ Ubuntu/Debian:

   ```bash
   sudo apt-get install tesseract-ocr tesseract-ocr-vie tesseract-ocr-eng
   ```

2. Cài thư viện. Tạo `app/.env` với `CLAUDE_API_KEY=...`. Có thể thêm `CLAUDE_MODEL` và `CLAUDE_BASE_URL` (xem `.env.example`).

   ```bash
   cd app
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   python main.py
   ```

3. Mở địa chỉ local được in ra ở terminal.

## Chạy trên Windows (PowerShell)

1. Cài Python 3.10+ và Tesseract OCR. Khi cài Tesseract, chọn thêm dữ liệu ngôn ngữ **English** và **Vietnamese**, đồng thời thêm thư mục chứa `tesseract.exe` vào biến môi trường `Path`. Mở lại PowerShell và kiểm tra:

   ```powershell
   tesseract --version
   tesseract --list-langs
   ```

   Danh sách ngôn ngữ cần có `eng` và `vie`.

2. Tạo `app/.env` với `CLAUDE_API_KEY=...` (có thể thêm `CLAUDE_MODEL` và `CLAUDE_BASE_URL`). Từ thư mục gốc dự án, cài thư viện và chạy app:

   ```powershell
   cd app
   py -3 -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   .\.venv\Scripts\python.exe main.py
   ```

3. Mở địa chỉ local được in ra trong PowerShell.

Ứng dụng hỗ trợ một file tối đa 10 MB và PDF tối đa 10 trang. Trang PDF chỉ có text được trích xuất trực tiếp; trang có ảnh hoặc không có text được OCR toàn trang để không bỏ sót nội dung ảnh trên PDF hỗn hợp. File tải lên và kết quả tạm được Gradio quản lý trong bộ nhớ đệm. Không đưa tài liệu nhạy cảm vào dịch vụ dịch bên ngoài nếu chưa được phép.

## Hiệu năng và kiểm tra

- Dịch theo lô tối đa 40 vùng / 4.000 ký tự, ánh xạ bằng ID và kiểm tra đủ kết quả trước khi ghép PDF. Vùng dài được chia theo câu hoặc khoảng trắng; chỉ token đơn dài quá giới hạn mới bị cắt cứng. Không gộp các chuỗi trùng nhau ở các ngữ cảnh khác nhau. Các lô chạy tuần tự để hạn chế vượt hạn mức API.
- Tái sử dụng client; timeout mạng 45 giây và tối đa một lần thử lại của SDK. Kết quả sai JSON/ID được thử lại một lần ở mức ứng dụng, sau đó báo lỗi. Đây không phải giới hạn thời gian tổng của tài liệu.
- Cache trong RAM: 16 tài liệu và 256 lô dịch gần nhất; thay đổi nội dung, ngôn ngữ, model, endpoint hoặc API key sẽ dùng khóa cache khác. Khởi động lại ứng dụng để xóa cache. Cache tài liệu giữ cả dữ liệu đầu vào và PDF đầu ra nên cần tính RAM khi triển khai nhiều người dùng.
- OCR dùng Tesseract PSM 11, PDF render ở 250 DPI, ảnh giới hạn 5.000 pixel mỗi chiều. Có timeout 60 giây; vùng tin cậy thấp được thử lại bằng crop PSM 7 và đảo nền tối. Ảnh xử lý hướng EXIF; chưa tự sửa mọi góc nghiêng của scan. Ghép dòng theo tọa độ, khoảng cách và dấu hiệu tiếp nối câu để tránh trộn cột.
- Prompt có thuật ngữ kỹ thuật Anh–Việt và tên riêng của mẫu SceneSearch. Cần điều chỉnh thuật ngữ cho lĩnh vực khác; kiểm tra ID không thay thế đánh giá ngữ nghĩa của người đọc.
- Hiển thị bản gốc ngay, cập nhật tiến độ từng trang và ghi thời gian OCR, dịch, dàn trang trong terminal.

Chạy kiểm tra không cần API thật từ thư mục gốc:

```bash
app/.venv/bin/python -m unittest discover -s app -p 'test_*.py' -v
```

Chạy lại đánh giá SceneSearch bằng API thật (có sử dụng hạn mức API), từ thư mục gốc:

```bash
app/.venv/bin/python app/evaluate_scenesearch.py
```

Kết quả OCR/bản dịch từng vùng, PDF và ảnh render nằm trong `app/evaluation/scenesearch/`. Kiểm thử OCR thật với mẫu này tự bỏ qua nếu file mẫu không có trong checkout.
