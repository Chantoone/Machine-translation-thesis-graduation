# Demo OCR và dịch tài liệu

Web demo một trang: tải PDF/PNG/JPG lên, đọc chữ, dịch và tải bản dịch `.txt`.

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

Ứng dụng hỗ trợ một file tối đa 10 MB và PDF tối đa 10 trang. Trang PDF có text được trích xuất trực tiếp; trang không có text được OCR. File tải lên và kết quả tạm được Gradio quản lý trong bộ nhớ đệm. Không đưa tài liệu nhạy cảm vào dịch vụ dịch bên ngoài nếu chưa được phép.
