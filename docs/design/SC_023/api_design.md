# THIẾT KẾ KIẾN TRÚC & API - SC_023 (ASSESSMENT HISTORY)

## 1. MỤC TIÊU (OBJECTIVE)
Tài liệu này xác định thiết kế kỹ thuật cấp thấp (Low-Level Design) cho tính năng SC_023 dựa trên `requirements.md`. Tài liệu này phục vụ cho đội ngũ Developer thực thi.

## 2. DATA MODELS (apps/medical/models.py)
*Ghi chú: Nếu model Assessment đã được tạo ở SC_022, cần bổ sung/xác minh các trường sau:*

```python
from django.db import models
from django.contrib.auth.models import User
from apps.residents.models import Resident

class Assessment(models.Model):
    ASSESSMENT_TYPES = [
        ('initial', 'Initial'),
        ('reassessment', 'Reassessment'),
    ]
    
    resident = models.ForeignKey(Resident, on_delete=models.CASCADE, related_name='assessments')
    version = models.PositiveIntegerField(default=1)
    assessment_type = models.CharField(max_length=20, choices=ASSESSMENT_TYPES, default='initial')
    assessment_date = models.DateField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.RESTRICT)
    total_adl_score = models.IntegerField(default=0)
    loc_tier = models.CharField(max_length=20, blank=True)
    is_locked = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-assessment_date', '-version'] # Sắp xếp mới nhất lên đầu
```

## 3. THIẾT KẾ CONTROLLER / VIEW (apps/medical/views.py)

### 3.1. Giao diện Assessment History (GET)
- **Hàm:** `assessment_history_view(request, resident_id)`
- **Decorator:** `@login_required`, `@permission_required('medical.view_assessment', raise_exception=True)`
- **Logic:**
  1. Truy vấn `Resident` dựa trên `resident_id`. Ném lỗi 404 nếu không tìm thấy.
  2. Truy vấn danh sách `Assessment` của resident đó: `assessments = Assessment.objects.filter(resident=resident).order_by('-version')`.
  3. Xử lý Logic Read-only: Template sẽ tự kiểm tra `assessment.is_locked`.
  4. Render template: `medical/sc_023_history.html` với context `{ 'resident': resident, 'assessments': assessments }`.

### 3.2. API Khởi tạo Reassessment mới (POST)
- **Hàm:** `create_reassessment_api(request, resident_id)`
- **Decorator:** `@login_required`, `@permission_required('medical.add_assessment', raise_exception=True)`
- **Logic:**
  1. Lấy bản ghi Assessment mới nhất của resident (sắp xếp theo `-version`).
  2. Copy dữ liệu (ADL, Vitals, Diagnoses) sang một Object Assessment mới.
  3. Gán `version = latest.version + 1`, `assessment_type = 'reassessment'`, `is_locked = False`.
  4. Lưu xuống DB và trả về Redirect (mã 302) chuyển hướng sang giao diện SC_022 (Edit Form) cho phiên bản mới này.

## 4. ROUTING (apps/medical/urls.py)
Bổ sung các URL patterns sau:
```python
path('residents/<str:resident_id>/assessments/', views.assessment_history_view, name='assessment_history'),
path('residents/<str:resident_id>/assessments/new/', views.create_reassessment_api, name='create_reassessment'),
```

## 5. THIẾT KẾ TEMPLATE (medical/sc_023_history.html)
- Kế thừa `base.html` (chứa Sidebar, chung layout của NHMS).
- Vùng Header: Breadcrumbs (Residents > [Tên] > Assessments), Tiêu đề, Nút "Select 2 to Compare" và Nút "+ New" (gọi POST form ẩn tới `create_reassessment`).
- Bảng Dữ Liệu (Table): 
  - Lặp qua `assessments`.
  - Hiển thị badge: `Initial` (màu xanh lam), `Reassessment` (màu tím).
  - Cột Action: Dùng câu điều kiện `{% if assessment.is_locked %}` để in ra "View • Compare" (tuyệt đối ẩn nút Edit/Delete để thỏa mãn NFR-02 Immutability).
