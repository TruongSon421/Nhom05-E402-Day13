# BÁO CÁO CÁ NHÂN - LAB DAY 13: OBSERVABILITY
**Học phần:** Trí tuệ nhân tạo thực chiến (Lab AI Thực Chiến)
**Sinh viên thực hiện:** Nông Trung Kiên (Member F)
**Vai trò:** Report Lead & System Integration

---

## I. TỔNG QUAN NHIỆM VỤ
Trong giai đoạn triển khai Lab Day 13 về hệ thống Quan sát (Observability) cho AI Agent, tôi đảm nhận vai trò Trưởng nhóm báo cáo (Report Lead) và Chuyên viên tích hợp hệ thống (System Integration). Nhiệm vụ chính bao gồm việc hoàn thiện cấu trúc báo cáo kỹ thuật (Blueprint Report), khôi phục và đồng bộ hóa các giao diện lập trình ứng dụng (API), đồng thời thiết lập các quy tắc cảnh báo (Alert Rules) nâng cao nhằm đảm bảo tính toàn vẹn và khả năng giám sát của hệ thống.

## II. CHI TIẾT CÁC CÔNG VIỆC THỰC HIỆN

### 1. Tích hợp và Đồng bộ hệ thống (System Integration)
Tôi đã tiến hành rà soát mã nguồn và xử lý các xung đột phát sinh trong quá trình hợp nhất (merge) mã nguồn của các thành viên. Các hạng mục kỹ thuật cụ thể bao gồm:
*   **Khôi phục API Routes:** Tái cấu trúc và tái triển khai các điểm cuối (endpoints) phục vụ giám sát bao gồm `/slo/status` và `/alerts/status` trong tệp [main.py](file:///e:/LabAIThucChien/Nhom05-E402-Day13/app/main.py). Việc này đảm bảo hệ thống có thể xuất dữ liệu trạng thái SLO và các thông báo cảnh báo dưới dạng JSON để phục vụ cho Dashboard.
*   **Tích hợp Dashboard:** Phối hợp cùng Member E để tích hợp đường dẫn hiển thị Dashboard trực tiếp trên nền tảng FastAPI, tạo điều kiện thuận lợi cho việc quan sát trực quan các chỉ số vận hành.

### 2. Thiết lập Hệ thống Cảnh báo (Alerting System)
Để đáp ứng yêu cầu khắc khe của rubric về việc có đủ 4 quy tắc cảnh báo, tôi đã trực tiếp phát triển quy tắc thứ tư:
*   **Phát triển Alert Rule #4 (Low Quality Score):** Thiết kế và cấu hình quy tắc cảnh báo về chất lượng phản hồi LLM khi giá trị trung bình định lượng (`quality_score_avg`) xuống dưới ngưỡng 0.60. 
*   **Triển khai logic đánh giá:** Lập trình hàm `evaluate_low_quality_score_alert()` trong module [alert_evaluator.py](file:///e:/LabAIThucChien/Nhom05-E402-Day13/app/alert_evaluator.py), kết nối dữ liệu từ metrics tới hệ thống đánh giá trạng thái firing/pending.
*   **Xây dựng Runbook kỹ thuật:** Soạn thảo tài liệu hướng dẫn xử lý sự cố (Runbook) chi tiết cho cảnh báo chất lượng thấp trong tệp [alerts.md](file:///e:/LabAIThucChien/Nhom05-E402-Day13/docs/alerts.md), định nghĩa rõ các bước kiểm tra (First checks) và biện pháp giảm thiểu (Mitigation).

### 3. Công tác Tài liệu và Phân tích Sự cố (Report Lead)
Với vai trò Report Lead, tôi đã hoàn thiện khung báo cáo [blueprint-template.md](file:///e:/LabAIThucChien/Nhom05-E402-Day13/docs/blueprint-template.md) với các nội dung mang tính học thuật và phân tích sâu:
*   **Phân tích Incident Response:** Tổng hợp và viết báo cáo cho 3 kịch bản sự cố mô phỏng (`rag_slow`, `tool_fail`, `cost_spike`). Tôi đã áp dụng phương pháp phân tích nguyên nhân gốc rễ (Root Cause Analysis) dựa trên dữ liệu từ Langfuse Trace Waterfall và Log line minh chứng.
*   **Xây dựng Hướng dẫn Evidence:** Soạn thảo tệp [guide-evidence.md](file:///e:/LabAIThucChien/Nhom05-E402-Day13/guide-evidence.md) cung cấp quy trình tác nghiệp chuẩn cho các thành viên trong việc thu thập bằng chứng vận hành, đảm bảo hồ sơ nộp bài đạt điểm tối đa theo tiêu chuẩn của giảng viên.
*   **Quản trị trạng thái nhóm:** Duy trì tài liệu [member-role-status.md](file:///e:/LabAIThucChien/Nhom05-E402-Day13/member-role-status.md) để theo dõi tiến độ và đảm bảo mọi thành viên đều hoàn thành đúng thời hạn các cam kết kỹ thuật.

## III. KẾT QUẢ ĐẠT ĐƯỢC
Thông qua nỗ lực thực hiện các nhiệm vụ trên, hệ thống Observability của Nhóm 5 đã đạt được các cột mốc quan trọng:
1.  **Validation Score:** Hệ thống đạt điểm tuyệt đối 100/100 khi chạy script kiểm tra tính hợp lệ của logs.
2.  **Tính sẵn sàng:** Các API giám sát hoạt động ổn định, cung cấp dữ liệu real-time chính xác cho Dashboard.
3.  **Tính bao quát:** Hệ thống cảnh báo bao phủ đầy đủ 4 lớp chỉ số quan trọng (Latency, Error Rate, Cost, Quality).

## IV. TỰ ĐÁNH GIÁ VÀ KẾT LUẬN
Bản thân tôi đã hoàn thành toàn bộ các hạng mục kỹ thuật và tài liệu được phân công. Sự phối hợp chặt chẽ giữa việc thực thi mã nguồn và tài liệu hóa quy trình đã giúp hệ thống không chỉ hoạt động tốt về mặt kỹ thuật mà còn có khả năng giải trình (explainability) cao thông qua các báo cáo chi tiết. Đây là nền tảng quan trọng để vận hành các AI Agent một cách an toàn và có thể kiểm soát được trong môi trường thực tế.

**Xác nhận sinh viên:**
*Nông Trung Kiên*
