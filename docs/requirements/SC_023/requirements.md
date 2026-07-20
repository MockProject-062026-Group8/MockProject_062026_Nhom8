# BÁO CÁO PHÂN TÍCH NGHIỆP VỤ & CẤU TRÚC DỮ LIỆU - SC_023 (ASSESSMENT HISTORY)

## 1. TỔNG QUAN (OVERVIEW)
- **Tên tính năng:** SC_023 — Lịch sử đánh giá cư dân (Assessment History).
- **Mục tiêu:** Cung cấp giao diện theo dõi lịch sử các bản đánh giá (Initial Assessment, Reassessment) của một cư dân cụ thể, hỗ trợ việc so sánh (Compare) và bắt đầu một kỳ đánh giá lại (Reassessment) theo quy định y tế.
- **Tuân thủ luật (Rules Pack):** 
  - **BR-03:** Tần suất đánh giá lại định kỳ mỗi 90 ngày.
  - **BR-05 / NFR-02 (Immutability):** Hồ sơ đã ký (e-signed) phải bị khóa (`is_locked = True`), tuyệt đối không được sửa/xóa.
  - **NFR-01 (HIPAA):** Bảo mật RBAC, giới hạn quyền truy cập bệnh án.

---

## 2. PHÂN TÍCH CẤU TRÚC DỮ LIỆU (SCHEMA MAPPING)

Tính năng này yêu cầu truy vấn liên thông (JOIN) giữa module `medical` và `residents`.

### 2.1. Nguồn dữ liệu từ `apps/residents/models.py`
- Bảng `Resident`:
  - `resident_id`: Mã định danh cư dân.
  - `full_name`: Tên đầy đủ hiển thị trên Header (VD: "Robert Hayes").

### 2.2. Nguồn dữ liệu từ `apps/medical/models.py`
Để đáp ứng Wireframe SC_023, model `Assessment` (hoặc tương đương) phải chứa (hoặc được trích xuất) các trường dữ liệu cốt lõi sau:
- **`resident`**: `models.ForeignKey('residents.Resident', on_delete=models.CASCADE, related_name='assessments')`
- **`version`**: `models.PositiveIntegerField()` (Đánh dấu phiên bản v1, v2, v3...).
- **`assessment_type`**: `models.CharField(choices=[('initial', 'Initial'), ('reassessment', 'Reassessment')])`.
- **`assessment_date`**: `models.DateField(auto_now_add=True)` (Ngày thực hiện đánh giá).
- **`author`**: `models.ForeignKey(User, on_delete=models.RESTRICT)` (Người lập, VD: "Anna Lee, RN").
- **`total_adl_score`**: `models.IntegerField()` (Tổng điểm ADL, VD: 20/32).
- **`loc_tier`**: `models.CharField()` (Phân cấp chăm sóc dựa trên ADL, VD: "Level 3").
- **`is_locked`**: `models.BooleanField(default=False)` (Cờ hiệu khóa hồ sơ).
- **`vitals`**: (Tùy chọn hiển thị chi tiết khi View).

---

## 3. CƠ CHẾ BẢO MẬT & PHÂN QUYỀN (RBAC & HIPAA)
1. **Phân quyền truy cập (RBAC):**
   - View `AssessmentHistory` yêu cầu user phải có role là **Nurse** hoặc **Doctor/Admin** (`@permission_required('medical.view_assessment')`).
   - Yêu cầu kiểm tra chéo cơ sở (Facility Check): User chỉ được xem lịch sử đánh giá của Resident thuộc cùng Facility.
2. **Cơ chế Read-only (Luật Bất Biến BR-05):**
   - Khi truy vấn danh sách Assessment, hệ thống sẽ kiểm tra cờ `is_locked`. 
   - **Với các bản ghi `is_locked == True`**: UI Front-end bắt buộc không render các nút "Edit" hay "Delete". Thay vào đó, chỉ render nút "View • Compare" dạng Hyperlink Read-only.
   - **Bảo vệ ở tầng Backend (API/Controller):** Bất kỳ request `PUT/PATCH/DELETE` nào nhắm vào `Assessment` có `is_locked == True` đều bị backend từ chối với mã lỗi `HTTP 403 Forbidden`.

---

## 4. NGHIỆP VỤ REASSESSMENT & COMPARE
- **Nút "+ New" (Tạo Reassessment mới):** 
  - Khởi tạo form Assessment mới, sao chép (pre-fill) tự động toàn bộ dữ liệu (ADL, IADL, Diagnoses...) từ bản đánh giá **mới nhất** (ví dụ v3) để y tá điều chỉnh thay vì nhập lại từ đầu.
  - Sau khi lưu, phiên bản mới sẽ được đánh là `v4` và loại là `Reassessment`.
- **Tính năng Compare:** Chọn 2 bản ghi bất kỳ trong lịch sử để kích hoạt giao diện đối chiếu sự thay đổi điểm số ADL/Vitals giữa 2 chu kỳ (so sánh tiến triển bệnh).
