# RELEASE NOTE: SC_023 Assessment History

**Phiên bản:** 1.0.0
**Ngày phát hành:** 13/07/2026
**Người thực hiện:** Senior DevOps (Antigravity Agent)
**Mã Ticket (Feature ID):** SC_023
**Nhánh Git (Branch):** `feature/SC_023-assessment-history`

---

## 1. Tóm tắt Tính năng Phát hành (Feature Summary)
Tính năng SC_023 (Lịch sử Đánh giá Cư dân) cung cấp màn hình giao diện liệt kê toàn bộ các bản báo cáo sức khỏe (Initial & Reassessment) của một bệnh nhân theo thời gian thực.
Được thiết kế để tối ưu hóa quy trình theo dõi chỉ số ADL, tính năng này giúp các Y tá và Quản trị viên dễ dàng tra cứu, đối chiếu (Compare) dữ liệu sức khỏe, đồng thời tự động hóa hoàn toàn quy trình tạo Reassessment mới theo đúng tần suất 90 ngày của nghiệp vụ.

## 2. Danh sách API / Endpoint bị Tác động
Các Route mới được khai báo trong `apps/medical/urls.py` và map tới `apps/medical/views.py`:

- **`GET /medical/residents/<resident_id>/assessments/`**
  - **Tên (Name):** `medical:assessment_history`
  - **Nhiệm vụ:** Trả về giao diện danh sách các bản đánh giá của cư dân tương ứng, được sắp xếp thứ tự mới nhất (phiên bản cao nhất) lên đầu.
- **`POST /medical/residents/<resident_id>/assessments/new/`**
  - **Tên (Name):** `medical:create_reassessment`
  - **Nhiệm vụ:** Sao chép (Clone) bản đánh giá gần nhất thành một phiên bản nháp (Draft) hoàn toàn mới, tự động kích hoạt loại `Reassessment` và trả về Redirect (mã 302).

## 3. Cấu trúc Bảng Dữ liệu thay đổi (SSMS 22)
Khởi tạo bảng mới trên cơ sở dữ liệu Microsoft SQL Server (hoặc SQLite môi trường Dev) để quản lý Lịch sử Đánh giá, định nghĩa tại `apps/medical/models.py`:

- **Table (Model): `medical_assessment`**
  - `id`: BigAutoField (Primary Key)
  - `resident_id`: Khóa ngoại (ForeignKey) tham chiếu tới bảng `residents_resident` (CASCADE).
  - `version`: Interger, mặc định = 1 (Phiên bản của bản đánh giá).
  - `assessment_type`: CharField, gồm 2 loại ('initial', 'reassessment').
  - `assessment_date`: DateField, ngày giờ lập phiếu (Tự động gán).
  - `author_id`: Khóa ngoại (ForeignKey) tham chiếu tới bảng `auth_user` của hệ thống (RESTRICT).
  - `total_adl_score`: Integer, điểm đánh giá tổng hợp ADL.
  - `loc_tier`: CharField, phân cấp theo mức độ chăm sóc (Ví dụ: Level 1, Level 2, Level 3).
  - `is_locked`: BooleanField, mặc định = False (Cờ khóa dữ liệu chống thay đổi).

## 4. Các Lưu ý Đặc biệt Về Phân quyền & Bảo mật (RBAC & HIPAA)
Theo quy định y tế khắt khe của hệ thống, tính năng đã tích hợp các cơ chế an ninh sau:
- **Kiểm soát Truy cập (RBAC):** 
  - Giao diện xem lịch sử (GET) được bảo vệ bởi `@permission_required('medical.view_assessment')`.
  - Luồng tạo mới (POST Reassessment) được bảo vệ bởi `@permission_required('medical.add_assessment')`.
  - Những tài khoản không có quyền hợp lệ sẽ nhận mã lỗi `HTTP 403 Forbidden`.
- **Luật Bất Biến Biểu Mẫu (Immutability - BR-05):**
  - Các bản ghi Assessment đã được đánh dấu `is_locked = True` sẽ bị vô hiệu hóa hoàn toàn khả năng chỉnh sửa trên giao diện `sc_023_history.html` (chỉ cung cấp tính năng "View • Compare" dưới dạng Read-Only). 
  - Khi Y tá kích hoạt "Reassessment", bản ghi tạo ra (clone) sẽ luôn được gán `is_locked = False` để có thể điền các thông số khám mới.
