# 📸 Hướng dẫn chụp Evidence & Nộp bài – Lab Day 13 (Observability)

**Người thực hiện:** Nông Trung Kiên (Member F – Demo Lead & Report)
**Dự án:** Nhóm 05 - E402-Day13
**Trạng thái:** Giả định mọi tính năng đã hoàn thiện.

Tài liệu này hướng dẫn chi tiết cách Member F (Kiên) phối hợp với các thành viên để lấy bằng chứng (evidence) và hoàn thiện báo cáo `blueprint-template.md`.

---

## 🛠️ Bước chuẩn bị chung (Trước khi chụp)

Trước khi chụp bất kỳ ảnh nào, cần tạo dữ liệu mẫu để log và trace có nội dung phong phú:

1. **Khởi chạy Server:**
   ```bash
   uvicorn app.main:app --reload
   ```

2. **Gửi dữ liệu mẫu (Load Test):**
   Chạy script để tạo ít nhất 20 requests có correlation ID:
   ```bash
   python scripts/load_test.py
   ```

3. **Tạo folder lưu trữ:**
   ```bash
   mkdir docs\evidence
   ```

---

## 📽️ Danh sách Evidence chi tiết từng phần

### 1. Correlation ID (Minh chứng cho Member A)
*   **Mục tiêu:** Hiển thị log JSON có chứa trường `correlation_id` dạng `req-xxxxxxxx`.
*   **Cách chụp:**
    *   Mở file `data/logs.jsonl`.
    *   Sử dụng lệnh sau để lọc ra 1 dòng đẹp nhất:
        ```bash
        python -c "import json; f=open('data/logs.jsonl'); [print(json.dumps(json.loads(l), indent=2, ensure_ascii=False)) for l in f if 'correlation_id' in l]; f.close()"
        ```
    *   **Ảnh cần chụp:** Chụp màn hình Terminal hiển thị cấu trúc JSON rõ ràng.
    *   **Lưu tên:** `docs/evidence/correlation_id.png`

### 2. PII Redaction (Minh chứng cho Member A)
*   **Mục tiêu:** Chứng minh dữ liệu nhạy cảm (Email, SĐT) đã bị ẩn (`[REDACTED]`) trước khi ghi log.
*   **Cách chụp:**
    *   Gửi một request có chứa PII:
        ```bash
        curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d "{\"message\":\"Số điện thoại của tôi là 0912345678 và email test@gmail.com\", \"user_id\":\"kien_nhom5\", \"session_id\":\"s01\", \"feature\":\"qa\", \"model\":\"gpt-4\"}"
        ```
    *   Kiểm tra dòng log mới nhất trong `data/logs.jsonl`.
    *   **Ảnh cần chụp:** Dòng log JSON mà phần tin nhắn (message) đã bị thay bằng `[REDACTED]`.
    *   **Lưu tên:** `docs/evidence/pii_redaction.png`

### 3. Langfuse Traces (Minh chứng cho Member B)
*   **Mục tiêu:** Show danh sách traces và chi tiết waterfall.
*   **Cách chụp:**
    *   Truy cập [cloud.langfuse.com](https://cloud.langfuse.com).
    *   **Ảnh 1 (Trace List):** Chụp danh sách các trace (phải có > 10 traces), cột User phải là ID đã được hash.
        *   *Lưu tên:* `docs/evidence/langfuse_trace_list.png`
    *   **Ảnh 2 (Waterfall):** Click vào 1 trace cụ thể để xem các bước: `agent.run` -> `retrieve` -> `generate`.
        *   *Lưu tên:* `docs/evidence/langfuse_trace_waterfall.png`

### 4. Alert Rules & Runbook (Minh chứng cho Member C)
*   **Mục tiêu:** Show cấu hình Alert và link tới hướng dẫn xử lý (Runbook).
*   **Cách chụp:**
    *   Mở file `config/alert_rules.yaml`.
    *   **Ảnh cần chụp:** Nội dung file YAML hiển thị đủ các rule (Latency, Error Rate, Cost, Quality).
    *   **Lưu tên:** `docs/evidence/alert_rules.png`
    *   *Lưu ý:* Phải kiểm tra file `docs/alerts.md` có link tương ứng trong blueprint.

### 5. Dashboard 6 Panels (Minh chứng cho Member D & E)
*   **Mục tiêu:** Giao diện Dashboard đẹp, đủ 6 biểu đồ và có đường kẻ SLO (đường đỏ).
*   **Cách chụp:**
    *   Mở trình duyệt: `http://localhost:8000/dashboard`
    *   Đợi khoảng 1 phút để dữ liệu đổ về (auto-refresh).
    *   **Ảnh cần chụp:** Toàn bộ trang Dashboard hiển thị rõ 6 panel: Latency, Traffic, Errors, Cost, Tokens, Quality.
    *   **Lưu tên:** `docs/evidence/dashboard_6panels.png`

### 6. Validation Score (Bằng chứng tổng hợp)
*   **Mục tiêu:** Chứng minh toàn bộ log đạt chuẩn 100/100.
*   **Cách chụp:**
    *   Chạy script kiểm tra:
        ```bash
        python scripts/validate_logs.py
        ```
    *   **Ảnh cần chụp:** Kết quả `Total Score: 100/100` và `Status: SUCCESS`.
    *   **Lưu tên:** `docs/evidence/validate_logs_100.png`

---

## 📝 Công việc cụ thể của Member F (Kiên) để hoàn tất Task

Sau khi đã có đủ bộ ảnh trên, Kiên cần thực hiện các bước sau:

### Bước 1: Cập nhật Blueprint Report
Mở file `docs/blueprint-template.md` và điền chính xác các thông tin:
- [ ] Điền tên đầy đủ các thành viên D, E, F.
- [ ] Cập nhật [TOTAL_TRACES_COUNT]: số lượng trace thực tế trên Langfuse (ví dụ: 25).
- [ ] Kiểm tra các đường dẫn ảnh đã khớp với folder `docs/evidence/` chưa.
- [ ] **Mục 4 (Incident Response):** Đây là phần quan trọng nhất của Kiên. Hãy mô phỏng một sự cố (ví dụ: RAG chậm) và viết cách phát hiện qua Dashboard/Trace và cách fix.

### Bước 2: Chuẩn bị Demo Script (8 Phút)
Kiên sẽ là người điều phối buổi thuyết trình. Kịch bản đề xuất:
1. **Phút 1:** Giới thiệu nhóm và kiến trúc Observability (Logging, Tracing, Metrics, Alerts).
2. **Phút 2-3 (Member A+B):** Show log có correlation và Langfuse waterfall.
3. **Phút 4-5 (Member C+D):** Show Dashboard real-time và cách Alert kích hoạt khi hạ ngưỡng SLO.
4. **Phút 6-7 (Kiên - Incident):** Thực hiện "Inject Incident" (làm chậm RAG) -> Show Dashboard vọt lên đỏ -> Kiểm tra Trace thấy lỗi ở đâu -> Fix.
5. **Phút 8:** Kết luận và show điểm Validation 100/100.

### Bước 3: Kiểm tra cuối cùng (Final Push)
```bash
git add docs/evidence/*.png
git add docs/blueprint-template.md
git add guide-evidence.md
git commit -m "docs: finalize evidence and report for Day 13 - Nông Trung Kiên"
git push origin your-branch
```

---
> [!IMPORTANT]
> **Lưu ý:** Luôn đảm bảo correlation_id trong log và trace đồng nhất để có thể giải trình khi giảng viên hỏi "Làm sao biết dòng log này thuộc về trace nào?".
