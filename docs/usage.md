
# Usage Guide: SC-022 Initial Assessment

## 1. Prerequisites
- You must be logged in as a user with the **Nurse** or **Clinical Admin** role.
- The Resident must already be created in the system and assigned to a room.

## 2. Navigating to the Assessment
1. Open the NHMS portal.
2. Click on **Residents** in the left sidebar.
3. Search for and select the resident (e.g., Elena Ramos).
4. Click on **New Admission Flow** and select **Step 3: Initial Assessment**.

## 3. Completing the Form
- **ADL Scoring**: For each of the 8 activities (Bed Mobility, Transfer, etc.), select the appropriate radio button representing the resident's independence level (0 to 4). The subtotal will calculate automatically in real-time.
- **IADL Scoring**: For each instrumental activity, select whether the resident is Dependent (0) or Independent (1).
- **Diagnoses**: 
  - Click **+ Add Diagnosis**.
  - Type the diagnosis name and ICD-10 code.
  - Click **Add**. It will appear as a bullet point in the list.
- **Allergies**: Type allergies separated by commas. If none, leave as "NKDA".
- **Vitals**: Input Blood Pressure (Sys/Dia), Heart Rate, Temperature, Weight, and Height in the provided inline fields.
- **Cognitive Status**: Select the single radio button that best describes the resident's mental status upon admission.
- **Clinical Notes**: Add any narrative observations that support the ADL scoring.

## 4. Saving and Locking
- Click the blue **Save Assessment → triggers LOC calc** button at the bottom of the screen.
- **WARNING**: Once saved, the assessment will be cryptographically signed and locked. You will not be able to edit it. If an error was made, you must contact a Clinical Admin to initiate a formal Amendment.
- Upon successful save, you will be redirected to the Resident Dashboard, and the new Care Level (LOC) will be displayed.

# Quy trình Phát triển Tính năng (Multi-Agent Workflow)

Tài liệu này quy định quy trình chuẩn từ lúc nhận yêu cầu (Ticket) cho đến khi đóng gói mã nguồn và tạo Pull Request. Tất cả các thành viên (Developer, QA, DevOps) và Agent cần tuân thủ nghiêm ngặt để đảm bảo chất lượng hệ thống.

---

## 1. QUY TẮC ĐẶT TÊN & CẤU TRÚC (Naming Conventions)

Để thống nhất trên toàn dự án (tránh tình trạng PR, Branch hoặc tên file lộn xộn), hệ thống quy định các chuẩn sau:

### 1.1. Quy tắc đặt tên Branch (Branching)
* **Tính năng mới (Feature):** `feature/[Mã_Ticket]-[tên-tính-năng-viết-thường-cách-nhau-bằng-gạch-ngang]`
  * *Ví dụ:* `feature/SC_024-loc-classification`
* **Sửa lỗi (Bugfix):** `bugfix/[Mã_Ticket]-[tên-lỗi]`
* **Sửa lỗi nóng (Hotfix):** `hotfix/[Mã_Ticket]-[tên-lỗi]`

### 1.2. Quy tắc Commit Message & Pull Request
Sử dụng chuẩn Conventional Commits kết hợp với Mã Ticket:
* **Định dạng:** `<type>(<scope>): implement <Mã_Ticket> <Tên ngắn gọn>`
* **Các type phổ biến:** `feat` (tính năng mới), `fix` (sửa lỗi), `docs` (tài liệu), `refactor` (tối ưu code), `test` (viết test).
* **Scope:** Thường là tên app (ví dụ: `medical`, `billing`, `residents`).
* **Ví dụ:**
  * `feat(medical): implement SC_024 LOC Classification`
  * `fix(billing): resolve SC_030 calculation error`
  * `docs: update release notes and change history for SC_024`

### 1.3. Cấu trúc thư mục Tài liệu (Documentation)
Toàn bộ tài liệu phân tích, thiết kế và phát hành phải được lưu trữ trong thư mục `docs/` theo đúng cấu trúc sau (không đặt tên tùy tiện):
* `docs/requirements/[Mã_Ticket]/requirements.md` (Tài liệu nghiệp vụ / BRD)
* `docs/design/[Mã_Ticket]/ui_design.md` (Thiết kế giao diện)
* `docs/design/[Mã_Ticket]/api_design.md` (Thiết kế API / Database)
* `docs/release/[Mã_Ticket]/config.md` (Cấu hình môi trường)
* `docs/release/[Mã_Ticket]/release.md` (Release notes)

---

## 2. QUY TRÌNH 7 BƯỚC THỰC HIỆN TICKET

### Bước 0: Khởi tạo Branch (Lead)
* **Mục tiêu:** Tạo không gian làm việc an toàn, độc lập cho tính năng mới.
* **Tác vụ:**
  1. Pull code mới nhất từ nhánh `dev`.
  2. Tạo nhánh mới theo đúng Quy tắc đặt tên Branch ở mục 1.1.

### Bước 1: Phân tích Nghiệp vụ (System Architect)
* **Mục tiêu:** Diễn dịch yêu cầu người dùng thành tài liệu yêu cầu (BRD).
* **Tác vụ:** Lập tài liệu phân tích, định nghĩa luồng dữ liệu, luật bất biến (Business Rules).
* **Kết xuất:** Sinh file `docs/requirements/[Mã_Ticket]/requirements.md`. Dừng lại chờ User duyệt.

### Bước 2: Thiết kế Hệ thống
* **Bước 2.1: Thiết kế Giao diện (UI/UX)**
  * Sinh file `docs/design/[Mã_Ticket]/ui_design.md`.
* **Bước 2.2: Thiết kế API & Database (DB Schema)**
  * Sinh file `docs/design/[Mã_Ticket]/api_design.md`.

### Bước 3: Lập trình Mã nguồn (Senior Developer)
* **Mục tiêu:** Hiện thực hóa các bản thiết kế 2.1 và 2.2 thành mã nguồn thật.
* **Tác vụ:**
  1. Khởi tạo/Cập nhật code tại `apps/[tên_app]/models.py`, `views.py`, `urls.py`.
  2. Xây dựng giao diện tại `apps/[tên_app]/templates/...`
  3. Chạy `python manage.py makemigrations` và `migrate`.
* **Kết xuất:** Mã nguồn hoàn chỉnh, sẵn sàng chạy.

### Bước 4: Kiểm thử Tự động & QA (Senior QA/QC)
* **Mục tiêu:** Đảm bảo mã nguồn hoạt động chính xác.
* **Tác vụ:** Viết Test Case tại `apps/[tên_app]/tests.py` và chạy lệnh `python manage.py test`.
* **Kết xuất:** Báo cáo Unit Test thành công 100%.

### Bước 5: Cấu hình Môi trường & Release Note (Senior DevOps)
* **Mục tiêu:** Chuẩn bị tài liệu kỹ thuật vận hành và hướng dẫn triển khai.
* **Tác vụ:**
  1. Viết thông số môi trường vào `docs/release/[Mã_Ticket]/config.md`.
  2. Tổng hợp thay đổi vào `docs/release/[Mã_Ticket]/release.md`.
* **Kết xuất:** Hồ sơ cấu hình và Release Note rõ ràng.

### Bước 6: Đóng gói Commit & Ghi Lịch sử (Senior DevOps)
* **Mục tiêu:** Đóng gói phiên bản thành các commit tiêu chuẩn và cập nhật nhật ký.
* **Tác vụ:**
  1. Commit mã nguồn (tuân thủ mục 1.2).
  2. Chèn dòng Log mới vào bảng trong `change_history.md`.
  3. Commit thứ hai dành riêng cho file Lịch sử & Release.

### Bước 7: Push Mã Nguồn & Rà Soát Tổng Thể (Senior DevOps & Lead)

* **Mục tiêu:** Đưa mã nguồn lên Remote Repository và mở Pull Request.
* **Tác vụ:**
  1. Rà soát lại toàn bộ vòng đời xem có vi phạm Quality Gate không.
  2. Thực thi lệnh đẩy mã nguồn: `git push origin [tên-nhánh]` (hoặc push qua fork).
  3. Tạo Pull Request với tên chuẩn theo mục 1.2.

* **Mục tiêu:** Đưa mã nguồn lên Remote Repository và mở Pull Request an toàn (không push trực tiếp vào origin).
* **Tác vụ:**
  1. Rà soát lại toàn bộ vòng đời xem có vi phạm Quality Gate không.
  2. Cấu hình fork (nếu chưa có): `gh repo fork --remote=true` (hoặc `git remote add fork [URL]`).
  3. Thực thi lệnh đẩy mã nguồn lên nhánh fork: `git push fork [tên-nhánh]`.

  4. Tạo Pull Request bằng lệnh GitHub CLI: `gh pr create -t "[Title]" -F pr_body.md -B dev`.

  4. Tạo Pull Request bằng lệnh GitHub CLI: `gh pr create -t "[Title]" -F pr_body.md -B dev --head [tên-user-fork]:[tên-nhánh]` (Lưu ý: Bắt buộc dùng cờ `--head` vì ta đang push lên fork thay vì origin).


* **Kết xuất:** Mã nguồn có mặt trên Git Server, Pull Request sẵn sàng review. Ticket chính thức đóng lại (Closed).

