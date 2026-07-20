# Cấu hình Môi trường & Triển khai SC_023 (Assessment History)

Tài liệu này đóng vai trò Hướng dẫn DevOps (Release Note) cho tính năng SC_023.

## 1. Cấu hình Di trú Dữ liệu (Database Migration)
- **Kết quả Migration:**
  - App `medical`: Model `Assessment` đã được thiết lập (hoặc xác thực) thông qua lệnh `python manage.py makemigrations medical`.
  - Do tính năng SC_022 và SC_023 chia sẻ chung model `Assessment`, file migration `0001_initial.py` đã tạo bản ghi ánh xạ lược đồ dữ liệu thành công.
  - Lệnh `python manage.py migrate` đã được thực thi và không báo lỗi. Database hiện tại đồng bộ hoàn toàn với Model.
- **Lưu ý Vận hành:** Khi triển khai tính năng lên môi trường Production (Staging/Live), DevOps bắt buộc phải thực thi lệnh `python manage.py migrate medical` trước khi restart Gunicorn/Uvicorn server để tránh lỗi bảng DB không tồn tại.

## 2. Cấu hình Kết nối Cơ sở Dữ liệu (SSMS 22)
- **Không sử dụng Docker Compose:** Hệ thống đang trỏ trực tiếp vào instance SQL Server trên Windows Server (`LAPTOP-AHUGE8A3\SQLEXPRESS`), do vậy dự án không sử dụng `docker-compose.yml` để vận hành DB.
- **Cấu hình `.env`:**
  - **DB_HOST**: `LAPTOP-AHUGE8A3\SQLEXPRESS`
  - **DB_PORT**: `1433` (Cổng mặc định của MS SQL Server)
  - **DB_NAME**: `nursing_home_db`
- **Lưu ý Vận hành (Production):** 
  - Tại file `.env` hiện tại, cờ `USE_SQLITE=True` đang được bật để phục vụ môi trường Dev/Test nhằm render giao diện.
  - Khi triển khai lên cụm máy chủ thật, DevOps phải đổi thành `USE_SQLITE=False` và điền bổ sung `DB_USER` cùng `DB_PASSWORD` vào file `.env` (Đã được định nghĩa sẵn trong `config/settings.py` sử dụng driver `ODBC Driver 17 for SQL Server`).

## 3. Checklist Triển khai (Deployment Checklist)
1. Kéo mã nguồn (Pull latest `feature/SC_023-assessment-history` hoặc từ nhánh `dev` sau khi merge PR).
2. Kiểm tra/sửa file `.env` (Đổi cấu hình về MS SQL Server thực tế).
3. Chạy lệnh: `python manage.py migrate`.
4. Khởi động lại Web Server.
