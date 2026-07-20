# Hướng dẫn sử dụng Multi-Agent Workflow (NHMS Fullstack Monolith)

Tài liệu này hướng dẫn chi tiết cách vận hành đội ngũ tổ hợp Agent chuyên biệt (Senior BA, Senior Research, Senior Architect, Senior Developer, Senior QA/QC, Senior DevOps) nhằm phát triển các tính năng Fullstack trên nền tảng ứng dụng nguyên khối Django Monolith phối hợp cơ sở dữ liệu Microsoft SQL Server (SSMS 22).

---

## 1. Khả năng tương thích (Compatibility)

Tất cả các AI Assistant chạy trong môi trường **Antigravity / Cursor / Claude Code** đều chia sẻ chung một "bộ não" kiến thức cốt lõi được lưu trữ tại file hệ thống:
* **`docs/antigravity_agent_rules.md`**: Định nghĩa bối cảnh nghiệp vụ y tế Mỹ (tiêu chuẩn bảo mật HIPAA, luật bất biến biểu mẫu y tế sau ký điện tử BR-05 chart lock), kiến trúc thư mục phân tầng Django Monolith, luồng thác dữ liệu tự động (Assessment Cascade) và các ràng buộc kỹ thuật tối cao.

---

## 2. Các bước vận hành (Workflow Steps)

> ⚠️ **Quy tắc kiểm soát chất lượng nghiêm ngặt (Quality Gate $\ge 9/10$):**
> Tại cuối mỗi bước phân tích, lập hồ sơ hoặc thiết kế tài liệu, Agent **BẮT BUỘC** phải lưu file vào đúng thư mục quy định, trình bày toàn bộ nội dung tệp tin và dừng luồng hoạt động lại (Sticky-Halt) để chờ người dùng đánh giá.
> * **Nếu Điểm số $\ge 9$ hoặc nhận từ khóa "PASS":** Agent tự động kích hoạt bước kế tiếp.
> * **Nếu Điểm số $< 9$:** Agent đứng yên tại chỗ, tiếp nhận feedback từ người dùng để điều chỉnh lại tài liệu cho tới khi đạt yêu cầu.
