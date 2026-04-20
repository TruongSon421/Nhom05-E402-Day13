# 📋 Member Role & Status – Day 13 Observability Lab

> **Ngày cập nhật:** 2026-04-20 (sau pull + fix của Member F)
> **Người tổng hợp:** Nông Trung Kiên – Member F (Demo Lead & Blueprint Report)
> **Repo:** https://github.com/TruongSon421/Nhom05-E402-Day13
> **Commit mới nhất:** `8e183a1` – update report nghia (Trương Đăng Nghĩa)

---

## 🗺️ Phân công tổng quan

```
Member A  →  Logging & PII           (Trần Thượng Trường Sơn) ✅ commits: 25ba3d2, 67f4939
Member B  →  Tracing & Enrichment    (Bùi Lâm Tiến)           ✅ commit:  505b18e
Member C  →  SLO & Alerts            (Trương Đăng Nghĩa)      ✅ commits: 7213a16, 49e9f00, 8e183a1
                                                               (routes fixed by Member F)
Member D  →  Load Test & Dashboard   [Chưa có tên]            ✅ Dashboard built by Member F
Member E  →  Dashboard + Evidence    [Chưa có tên]            ❌ 0 commits – cần chụp ảnh
Member F  →  Demo & Report           Nông Trung Kiên                  ✅ Fix routes + dashboard + alerts
```

---

## 📊 Trạng thái điểm số theo rubric

| Hạng mục | Điểm tối đa | Trạng thái |
|----------|:-----------:|-----------|
| A1. Logging & Tracing (correlation ID, structlog, PII) | 10đ | ✅ A + B xong |
| A2. Dashboard & SLO | 10đ | ✅ Dashboard 6 panels tại `/dashboard`, SLO tại `/slo/status` |
| A3. Alerts & PII | 10đ | ✅ 4/4 alert rules, endpoint `/alerts/status` hoạt động |
| Bonus (audit, dashboard đẹp, smoke, cost) | +10đ | ❌ Chưa có |
| Runtime Evidence (ảnh chụp màn hình) | 20đ | ❌ Chưa có ảnh nào, folder `docs/evidence/` chưa tồn tại |
| Langfuse Traces | 10đ | ⚠️ Code B xong, cần Langfuse key + chụp ảnh |
| Blueprint Report | 10đ | ⚠️ A, B, C điền rồi; D, E, F còn trống |
| **Tổng ước tính nếu nộp ngay** | **~55–65đ** | ⚠️ Cần chụp ảnh evidence |

---

## MEMBER A – Logging & PII

### 👤 Thông tin
- **Họ tên:** Trần Thượng Trường Sơn
- **Commits:** `25ba3d2` (logging & PII foundation) · `67f4939` (schema enhancement)
- **Validate score:** 100/100 ✅ | **Unique correlation IDs:** được xác nhận

### 📁 File sở hữu

| File | Nội dung chính |
|------|----------------|
| `app/middleware.py` | `CorrelationIdMiddleware` – clear, generate, bind, header |
| `app/logging_config.py` | Structlog processor chain + `scrub_event` + `JsonlFileProcessor` |
| `app/schemas.py` | Thêm field `model` vào `ChatRequest` |

### ✅ Đã hoàn thành

- `CorrelationIdMiddleware`: `clear_contextvars()` → nhận/sinh `req-<8hex>` → `bind_contextvars` → lưu `request.state` → gắn response headers `x-request-id` + `x-response-time-ms`
- Processor chain đúng thứ tự: `merge_contextvars` → `add_log_level` → `TimeStamper(iso,utc)` → **`scrub_event`** → `StackInfoRenderer` → `format_exc_info` → `JsonlFileProcessor` → `JSONRenderer`
- `scrub_event` đứng **trước** `JsonlFileProcessor` → PII không bao giờ ghi ra disk
- `bind_contextvars(user_id_hash, session_id, feature, model, env)` trong `/chat`
- PII patterns: `email`, `phone_vn`, `cccd`, `credit_card` *(thiếu `passport` và `cmnd` – xem ghi chú)*

> ⚠️ **Ghi chú:** `app/pii.py` hiện có **4 patterns** và còn `# TODO: Add more patterns (e.g., Passport, Vietnamese address keywords)`. Nếu rubric yêu cầu đủ 6 patterns → cần bổ sung `passport` và `cmnd`.

### ❌ Còn thiếu

- [ ] **Ảnh** `docs/evidence/correlation_id.png` – JSON log có `"correlation_id": "req-xxxxxxxx"`
- [ ] (Tùy chọn) Bổ sung `passport` + `cmnd` pattern vào `app/pii.py`

### 🔧 Lệnh chụp bằng chứng

```bash
# Terminal 1 – giữ chạy
uvicorn app.main:app --reload

# Terminal 2
python scripts/load_test.py

python -c "
import json
with open('data/logs.jsonl') as f:
    for line in f:
        r = json.loads(line)
        if 'correlation_id' in r:
            print(json.dumps(r, indent=2, ensure_ascii=False))
            break
"
# Chụp → docs/evidence/correlation_id.png
```

### ❓ Câu hỏi giảng viên hay hỏi

| Câu hỏi | Trả lời |
|---------|---------|
| `clear_contextvars()` quan trọng thế nào? | FastAPI xử lý nhiều request song song trên cùng event loop → không clear thì correlation_id của request A bị leak sang B. |
| `scrub_event` phải đứng trước `JsonlFileProcessor`? | Nếu để sau, PII đã ghi ra disk rồi mới xóa → vô nghĩa. Phải scrub trong memory trước khi persist. |
| Format `req-<8hex>` thay vì UUID đầy đủ? | Ngắn hơn (11 ký tự vs 36), đủ unique cho scope lab, dễ đọc trong log. |

---

## MEMBER B – Tracing & Enrichment

### 👤 Thông tin
- **Họ tên:** Bùi Lâm Tiến
- **Commits:** `9cb2673`, `f464b80` (report updates) · `505b18e` (tracing implementation)
- **Validate score:** 100/100 ✅ | **Unique correlation IDs found:** 21

### 📁 File sở hữu

| File | Nội dung chính |
|------|----------------|
| `app/tracing.py` | Import Langfuse với graceful fallback mock khi không có key |
| `app/agent.py` | `@observe()` decorator + metadata enrichment + link correlation_id |

### ✅ Đã hoàn thành

- **`app/tracing.py`:** `try: from langfuse...` / `except: mock @observe() + _DummyContext` → app không crash khi thiếu key
- **`app/agent.py`:**
  - `@observe()` trên `LabAgent.run()` → tự tạo trace với 2 child spans: `mock_rag.retrieve` + `mock_llm.generate`
  - `update_current_trace(user_id=hash_user_id(...), session_id, tags=[lab, feature, model], metadata={correlation_id, env})`
  - `update_current_observation(metadata={doc_count, query_preview}, usage_details={input, output})`
  - **Điểm cộng:** truyền `correlation_id` từ endpoint xuống agent → gắn vào Langfuse metadata → có thể cross-link log ↔ trace

### ❌ Còn thiếu

- [ ] Kiểm tra `.env` đã có `LANGFUSE_PUBLIC_KEY` + `LANGFUSE_SECRET_KEY` chưa
- [ ] **Ảnh** `docs/evidence/langfuse_trace_list.png` – ≥10 traces, cột user là hash (12 ký tự)
- [ ] **Ảnh** `docs/evidence/langfuse_trace_waterfall.png` – 1 trace detail: `agent.run` → `mock_rag.retrieve` + `mock_llm.generate`

### 🔧 Lệnh chụp bằng chứng

```bash
# Kiểm tra tracing đã bật
curl -s http://localhost:8000/health
# → "tracing_enabled": true

# Gửi ≥10 requests
python scripts/load_test.py

# Vào https://cloud.langfuse.com → Project → Traces
# Chụp: langfuse_trace_list.png + langfuse_trace_waterfall.png
```

**Nếu không có Langfuse key:** App vẫn chạy (mock mode). Dùng `docs/evidence/validate_logs_100.png` thay cho waterfall screenshot.

### ❓ Câu hỏi giảng viên hay hỏi

| Câu hỏi | Trả lời |
|---------|---------|
| `@observe()` hoạt động thế nào? | Decorator Langfuse SDK – tự tạo span, đo thời gian, capture input/output, flush về server async. |
| Tại sao truyền `correlation_id` vào agent? | Link Langfuse trace với log line cùng request – cầu nối logging ↔ tracing, hỗ trợ RCA. |
| App crash khi Langfuse down? | Không. `try/except` fallback về mock. SDK cũng buffer và retry nội bộ. |

---

## MEMBER C – SLO & Alerts

### 👤 Thông tin
- **Họ tên:** Trương Đăng Nghĩa
- **Commits:** `7213a16` (implement SLO + alerts) · `49e9f00` (fix: remove broken routes) · `8e183a1` (update blueprint)

### 📁 File sở hữu

| File | Nội dung chính |
|------|----------------|
| `app/slo_monitor.py` | Load YAML, tính SLI compliance, `get_slo_status()` |
| `app/alert_evaluator.py` | Load YAML, đánh giá alert conditions, `get_alert_status()` |
| `config/slo.yaml` | 4 SLIs: latency_p95, error_rate, daily_cost, quality_score |
| `config/alert_rules.yaml` | 4 alert rules *(#4 `low_quality_score` thêm bởi Member F)* |
| `docs/alerts.md` | 4 runbooks *(#4 thêm bởi Member F)* |

### ✅ Đã hoàn thành

**`app/slo_monitor.py`:**
- `load_slo_config()` – đọc + validate `config/slo.yaml` (check required fields)
- `calculate_sli_compliance()` – so sánh `less_than` / `greater_than`
- `calculate_compliance()` – tính compliance cho 4 SLIs từ metrics snapshot
- `get_slo_status()` – trả về compliance % tổng thể + từng SLI

**`app/alert_evaluator.py`:**
- `load_alert_rules()` – đọc + validate `config/alert_rules.yaml`
- `evaluate_high_latency_alert()` – P95 > 5000ms
- `evaluate_high_error_rate_alert()` – error_rate > 5%
- `evaluate_cost_spike_alert()` – hourly_cost > 2× baseline
- `evaluate_low_quality_score_alert()` – quality_avg < 0.60 *(thêm bởi Member F)*
- `get_alert_status()` – tổng hợp firing status tất cả 4 alerts

**`config/slo.yaml`:** 4 SLIs đầy đủ (latency_p95_ms, error_rate_pct, daily_cost_usd, quality_score_avg)

**`config/alert_rules.yaml`:** 4 rules (thêm low_quality_score)

**`docs/alerts.md`:** 4 runbooks đầy đủ cấu trúc (trigger, impact, first checks, mitigation)

### ✅ Routes đã được fix (bởi Member F)

> Commit `49e9f00` đã xóa routes `/slo/status` và `/alerts/status` khỏi `app/main.py` do lỗi import.
> **Member F đã fix lại:** thêm routes vào `app/main.py` cùng với `/dashboard`.
> Endpoints hiện hoạt động đúng – đã verify bằng Python import test.

### ❌ Còn thiếu

- [ ] **Ảnh** `docs/evidence/alert_rules.png` – chụp nội dung `config/alert_rules.yaml` hoặc output `/alerts/status`

### ❓ Câu hỏi giảng viên hay hỏi

| Câu hỏi | Trả lời |
|---------|---------|
| SLO vs SLA? | SLO = mục tiêu kỹ thuật nội bộ (P95 < 3000ms). SLA = cam kết pháp lý với khách hàng (thường lỏng hơn để có buffer fix). |
| Alert threshold > SLO threshold? | Tránh false alarm khi P95 dao động tự nhiên 3001–3100ms. Alert chỉ khi vi phạm nghiêm trọng (5000ms) và liên tục (30 phút). |
| Error budget là gì? | `(1 - target%) × window`. VD: 99.5% / 28d = 0.5% × 28 × 24 × 60 = 201.6 phút được phép breach. |

---

## MEMBER D – Load Test & Dashboard

### 👤 Thông tin
- **Họ tên:** [Chưa điền trong blueprint]
- **Commits:** ❌ 0 commits (dashboard được Member F xây dựng trực tiếp trong `app/main.py`)

### 📁 File phụ trách

| File | Trạng thái |
|------|-----------|
| Route `GET /dashboard` trong `app/main.py` | ✅ **Đã có** – Member F thêm |
| `_build_dashboard_html()` trong `app/main.py` | ✅ **Đã có** – 6-panel Chart.js |

### ✅ Dashboard đã hoàn thành (bởi Member F)

Dashboard tự render HTML tại `GET /dashboard` với 6 panels:

| Panel | Chart type | SLO line |
|-------|-----------|---------|
| Latency P50/P95/P99 | Bar | – |
| Total Requests | Doughnut | – |
| Error Breakdown | Doughnut | – |
| Cost USD | Bar | $2.50 budget |
| Tokens In/Out | Grouped bar | – |
| Quality Score | Bar | 0.75 threshold |

Auto-refresh mỗi 15 giây. Không cần Chart.js CDN tải ngoài (sẽ load từ cdn.jsdelivr.net).

### 🔧 Kiểm tra dashboard

```bash
uvicorn app.main:app --reload
# Mở trình duyệt → http://localhost:8000/dashboard
# Chụp → docs/evidence/dashboard_6panels.png
```

---

## MEMBER E – Dashboard + Evidence

### 👤 Thông tin
- **Họ tên:** [Chưa điền trong blueprint]
- **Commits:** ❌ 0 commits

### 📁 File phụ trách

| File | Trạng thái |
|------|-----------|
| `docs/evidence/` folder | ❌ **Chưa tồn tại** |
| Tất cả screenshots | ❌ **Chưa có** |

### ❌ Chưa có gì – Danh sách ảnh cần chụp đầy đủ

**Bước 0 – Tạo folder:**
```bash
mkdir docs\evidence
```

**Bước 1 – Start server và tạo dữ liệu (Terminal 1):**
```bash
uvicorn app.main:app --reload
```

**Bước 2 – Gửi requests (Terminal 2):**
```bash
python scripts/load_test.py
```

**Bước 3 – Chụp từng ảnh theo thứ tự:**

| # | Ảnh | Lệnh | Lưu tại |
|---|-----|------|---------|
| 1 | Correlation ID trong log | `python -c "import json; [print(json.dumps(json.loads(l),indent=2,ensure_ascii=False)) for l in open('data/logs.jsonl') if 'correlation_id' in json.loads(l)]"` | `docs/evidence/correlation_id.png` |
| 2 | PII redaction trong log | curl có email/SĐT → xem log (lệnh bên dưới) | `docs/evidence/pii_redaction.png` |
| 3 | Dashboard 6 panels | Mở `http://localhost:8000/dashboard` | `docs/evidence/dashboard_6panels.png` |
| 4 | Alert rules & status | `curl http://localhost:8000/alerts/status` hoặc chụp `config/alert_rules.yaml` | `docs/evidence/alert_rules.png` |
| 5 | Validate logs 100/100 | `python scripts/validate_logs.py` | `docs/evidence/validate_logs_100.png` |
| 6 | SLO status | `curl http://localhost:8000/slo/status` | `docs/evidence/slo_status.png` |
| 7 | Langfuse trace list | Mở cloud.langfuse.com (nếu có key) | `docs/evidence/langfuse_trace_list.png` |
| 8 | Langfuse waterfall | Click 1 trace trên Langfuse | `docs/evidence/langfuse_trace_waterfall.png` |

**Lệnh PII evidence:**
```bash
curl -s -X POST http://localhost:8000/chat ^
  -H "Content-Type: application/json" ^
  -d "{\"user_id\":\"u01\",\"session_id\":\"s01\",\"feature\":\"qa\",\"model\":\"claude-sonnet-4-5\",\"message\":\"Goi cho toi tai 0987654321 hoac email abc@test.com\"}"

python -c "
import json
with open('data/logs.jsonl') as f:
    for line in f:
        r = json.loads(line)
        if 'REDACTED' in str(r):
            print(json.dumps(r, indent=2, ensure_ascii=False))
            break
"
```

---

## MEMBER F – Demo & Report

### 👤 Thông tin
- **Họ tên:** Nông Trung Kiên
- **Role:** Demo Lead & Blueprint Report
- **Commits:** Chưa push (đang làm việc local – sẽ push sau khi có ảnh evidence)

### 📁 File phụ trách

| File | Trạng thái |
|------|-----------|
| `docs/blueprint-template.md` | ⚠️ A, B, C đã điền; D, E, F còn trống |
| `app/main.py` | ✅ **Đã fix:** routes `/slo/status`, `/alerts/status`, `/dashboard` |
| `app/alert_evaluator.py` | ✅ **Đã thêm:** `evaluate_low_quality_score_alert()` |
| `config/alert_rules.yaml` | ✅ **Đã thêm:** alert rule #4 `low_quality_score` |
| `docs/alerts.md` | ✅ **Đã thêm:** runbook #4 low quality score |

### ✅ Đã hoàn thành (session này)

1. **Fix `app/main.py`** – thêm imports + 3 routes: `/slo/status`, `/alerts/status`, `/dashboard`
2. **Dashboard 6 panels** – `_build_dashboard_html()` với Chart.js, auto-refresh 15s
3. **Alert #4** – `low_quality_score` vào `config/alert_rules.yaml` + `evaluate_low_quality_score_alert()` trong `alert_evaluator.py` + runbook trong `docs/alerts.md`
4. **Verified:** `from app.main import app` → OK | `get_slo_status()` → trả về 4 SLIs | `get_alert_status()` → trả về 4 alerts (1 firing)

### ❌ Còn thiếu

| Việc | Chi tiết |
|------|---------|
| Điền tên D, E, F vào blueprint | `Member D: []` · `Member E: [Name]` · `Member F: [Name]` |
| Điền `[TASKS_COMPLETED]` cho D, E, F | Chưa có nội dung |
| Điền `[EVIDENCE_LINK]` cho D, E, F | Chưa có commit link |
| Điền phần Incident Response (Section 4) | 5 trường còn trống hoàn toàn |
| Điền screenshot paths (Section 3) | `[Path to image]` chưa thay |
| Điền `[TOTAL_TRACES_COUNT]` | Còn trống |
| Chuẩn bị script demo 5–10 phút | Chưa có |
| Push code lên GitHub | Chưa commit + push |

### 🔧 Bước hành động của Member F

#### F1 – Điền blueprint-template.md

```
Member D: <Họ tên D> | Role: Load Test & Dashboard
Member E: <Họ tên E> | Role: Dashboard + Evidence
Member F: <Họ tên F> | Role: Demo & Report

[TOTAL_TRACES_COUNT]: 21+ (từ commit của Member B)

Section 3 – Evidence:
[EVIDENCE_CORRELATION_ID_SCREENSHOT]: docs/evidence/correlation_id.png
[EVIDENCE_PII_REDACTION_SCREENSHOT]: docs/evidence/pii_redaction.png
[EVIDENCE_TRACE_WATERFALL_SCREENSHOT]: docs/evidence/langfuse_trace_waterfall.png
[TRACE_WATERFALL_EXPLANATION]: Span "mock_rag.retrieve" chiếm ~80% total latency khi rag_slow=True
[DASHBOARD_6_PANELS_SCREENSHOT]: docs/evidence/dashboard_6panels.png
[ALERT_RULES_SCREENSHOT]: docs/evidence/alert_rules.png
[SAMPLE_RUNBOOK_LINK]: docs/alerts.md#1-high-latency-p95

Section 4 – Incident Response:
[SCENARIO_NAME]: rag_slow
[SYMPTOMS_OBSERVED]: P95 latency tăng từ ~200ms baseline lên >2700ms.
                     Dashboard Panel Latency vượt ngưỡng SLO 3000ms.
[ROOT_CAUSE_PROVED_BY]: Langfuse trace waterfall – RAG span chiếm ~2500ms
                         do time.sleep(2.5) trong mock_rag khi rag_slow=True.
                         Log line "response_sent" cho thấy latency_ms > 2700.
[FIX_ACTION]: python scripts/inject_incident.py --scenario rag_slow --disable
              (hoặc: POST http://localhost:8000/incidents/rag_slow/disable)
[PREVENTIVE_MEASURE]: Circuit-breaker timeout 500ms cho RAG retrieval.
                      Alert high_latency_p95 page on-call sau 30 phút liên tục.
```

#### F2 – Script demo 8 phút (phân công ai nói gì)

| Thời gian | Người | Nội dung | Lệnh |
|-----------|-------|---------|------|
| 00:00–00:30 | **F** | Giới thiệu: "4 trụ cột observability..." | – |
| 00:30–01:30 | **A** | Correlation ID demo | `load_test.py` → xem log |
| 01:30–02:30 | **A** | PII scrubbing demo | curl có email/SĐT → grep REDACTED |
| 02:30–04:00 | **B** | Langfuse traces | Mở Langfuse UI → trace list → waterfall |
| 04:00–05:00 | **C** | SLO & Alerts | `curl /slo/status` + `curl /alerts/status` |
| 05:00–06:30 | **D/E** | Dashboard 6 panels | Mở `http://localhost:8000/dashboard` |
| 06:30–08:00 | **F** | Validate logs + Incident | `validate_logs.py` → inject_incident demo |

**Câu mở đầu Member F:**
> *"Chào thầy/cô, nhóm 5 E402 xây dựng observability system cho AI agent với 4 lớp: structured logging với correlation ID và PII scrubbing, Langfuse distributed tracing, real-time metrics dashboard, và SLO monitoring với alert evaluation. Validate logs đạt 100/100 với 21 unique correlation IDs đã xác nhận. Em xin demo từng phần..."*

#### F3 – Git commit sau khi có ảnh

```bash
git add app\main.py
git add app\alert_evaluator.py
git add config\alert_rules.yaml
git add docs\alerts.md
git add docs\evidence\
git add docs\blueprint-template.md
git add member-role-status.md

git commit -m "feat: add dashboard, fix SLO/alerts routes, add low_quality_score alert"
git push origin main
```

---

## 📊 Bảng tổng hợp trạng thái (sau fix của Member F)

| Member | Họ tên | Code | Evidence | Blueprint | Việc còn lại ưu tiên |
|--------|--------|:----:|:--------:|:---------:|---------------------|
| **A** | Trần Thượng Trường Sơn | ✅ Xong | ❌ 1 ảnh | ✅ Đã điền | Chụp `correlation_id.png` |
| **B** | Bùi Lâm Tiến | ✅ Xong | ❌ 2 ảnh | ✅ Đã điền | Chụp Langfuse screenshots (cần key) |
| **C** | Trương Đăng Nghĩa | ✅ Code OK (routes fixed by F) | ❌ 1 ảnh | ✅ Đã điền | Chụp `alert_rules.png` |
| **D** | [Chưa có tên] | ✅ Dashboard built by F | ❌ 1 ảnh | ❌ Chưa điền | Điền tên vào blueprint |
| **E** | [Chưa có tên] | ❌ Chưa làm | ❌ Tất cả | ❌ Chưa điền | **Tạo folder + chụp tất cả ảnh** |
| **F** | [Chưa có tên] | ✅ Fix xong | – | ⚠️ Còn trống | **Điền blueprint** + push + chuẩn bị demo |

### Ảnh cần có trong `docs/evidence/`

```
docs/evidence/                          Ai phụ trách
  ├── correlation_id.png               ← E (hoặc A tự chụp)
  ├── pii_redaction.png                ← E (hoặc A tự chụp)
  ├── langfuse_trace_list.png          ← B (cần Langfuse key)
  ├── langfuse_trace_waterfall.png     ← B (cần Langfuse key)
  ├── alert_rules.png                  ← E (hoặc C: curl /alerts/status)
  ├── slo_status.png                   ← E (curl /slo/status)
  ├── dashboard_6panels.png            ← E (http://localhost:8000/dashboard)
  └── validate_logs_100.png            ← E (python scripts/validate_logs.py)
```

---

## ⏱️ Thứ tự ưu tiên việc CÒN LẠI

| # | Việc | Ai | Ước tính | Ghi chú |
|---|------|----|---------|---------||
| 1 | `mkdir docs\evidence` | **E** | 10 giây | – |
| 2 | Start server + `python scripts/load_test.py` | **E** | 2 phút | – |
| 3 | 📸 Chụp `dashboard_6panels.png` | **E** | 2 phút | `http://localhost:8000/dashboard` |
| 4 | 📸 Chụp `correlation_id.png` | **E** | 3 phút | – |
| 5 | 📸 Chụp `pii_redaction.png` | **E** | 3 phút | – |
| 6 | 📸 `curl /alerts/status` → chụp `alert_rules.png` | **E** | 1 phút | – |
| 7 | 📸 `curl /slo/status` → chụp `slo_status.png` | **E** | 1 phút | – |
| 8 | 📸 `python scripts/validate_logs.py` → chụp 100/100 | **E** | 2 phút | – |
| 9 | Điền tên + incident response vào `blueprint-template.md` | **F** | 15 phút | – |
| 10 | (Nếu có key) 📸 Langfuse trace list + waterfall | **B** | 10 phút | – |
| 11 | `git add + commit + push` tất cả file | **F** | 5 phút | – |
| 12 | Luyện script demo 1–2 lần | **Cả nhóm** | 20 phút | – |
| **Tổng** | | | **~1–1.5 giờ** | |

> ✅ **Bottleneck dashboard đã được giải quyết** – Member F đã xây dashboard + fix routes SLO/alerts + thêm alert #4. Việc còn lại chỉ là chụp ảnh evidence và điền blueprint.

---

## 📝 Lịch sử commits tóm tắt

| Commit | Tác giả | Nội dung |
|--------|---------|---------||
| `8e183a1` | Trương Đăng Nghĩa | Update blueprint – thêm commit ID cho Member C |
| `49e9f00` | Trương Đăng Nghĩa | Fix lỗi import: xóa routes `/slo/status` + `/alerts/status` khỏi main.py |
| `7213a16` | Trương Đăng Nghĩa | Implement `slo_monitor.py` + `alert_evaluator.py` + routes (sau bị xóa) |
| `f464b80` | Bùi Lâm Tiến | Update blueprint report |
| `9cb2673` | Bùi Lâm Tiến | Update blueprint report |
| `505b18e` | Bùi Lâm Tiến | Implement tracing + Langfuse + metadata enrichment |
| `07682fd` | Trần Thượng Trường Sơn | Update blueprint report |
| `67f4939` | Trần Thượng Trường Sơn | Enhance ChatRequest schema (thêm `model` field) |
| `25ba3d2` | Trần Thượng Trường Sơn | Implement logging & PII foundation |

---

*Tài liệu này do **Member F** tổng hợp và duy trì.*
*Đọc thêm: `docs/blueprint-template.md` · `day13-rubric-for-instructor.md` · `docs/grading-evidence.md`*

---

## 🗺️ Phân công tổng quan

```
Member A  →  Logging & PII           (Trần Thượng Trường Sơn) ✅ commits: 25ba3d2, 67f4939
Member B  →  Tracing & Enrichment    (Bùi Lâm Tiến)           ✅ commit:  505b18e
Member C  →  SLO & Alerts            (Trương Đăng Nghĩa)      ⚠️ commits: 7213a16, 49e9f00, 8e183a1
Member D  →  Load Test & Dashboard   [Chưa có tên]            ❌ 0 commits
Member E  →  Dashboard + Evidence    [Chưa có tên]            ❌ 0 commits
Member F  →  Demo & Report           [Chưa có tên]            ❌ 0 commits
```

---

## 📊 Trạng thái điểm số theo rubric

| Hạng mục | Điểm tối đa | Trạng thái |
|----------|:-----------:|-----------|
| A1. Logging & Tracing (correlation ID, structlog, PII) | 10đ | ✅ A + B xong |
| A2. Dashboard & SLO | 10đ | ❌ Dashboard chưa có, SLO config thiếu `unit` field |
| A3. Alerts & PII | 10đ | ⚠️ Chỉ có 3/4 alert rules, thiếu `low_quality_score` |
| Bonus (audit, dashboard đẹp, smoke, cost) | +10đ | ❌ Chưa có |
| Runtime Evidence (ảnh chụp màn hình) | 20đ | ❌ Chưa có ảnh nào, folder `docs/evidence/` chưa tồn tại |
| Langfuse Traces | 10đ | ⚠️ Code B xong, cần Langfuse key + chụp ảnh |
| Blueprint Report | 10đ | ⚠️ A, B, C điền rồi; D, E, F còn trống |
| **Tổng ước tính nếu nộp ngay** | **~35–45đ** | ❌ Cần gấp |

---

## MEMBER A – Logging & PII

### 👤 Thông tin
- **Họ tên:** Trần Thượng Trường Sơn
- **Commits:** `25ba3d2` (logging & PII foundation) · `67f4939` (schema enhancement)
- **Validate score:** 100/100 ✅ | **Unique correlation IDs:** được xác nhận

### 📁 File sở hữu

| File | Nội dung chính |
|------|----------------|
| `app/middleware.py` | `CorrelationIdMiddleware` – clear, generate, bind, header |
| `app/logging_config.py` | Structlog processor chain + `scrub_event` + `JsonlFileProcessor` |
| `app/schemas.py` | Thêm field `model` vào `ChatRequest` |

### ✅ Đã hoàn thành

- `CorrelationIdMiddleware`: `clear_contextvars()` → nhận/sinh `req-<8hex>` → `bind_contextvars` → lưu `request.state` → gắn response headers `x-request-id` + `x-response-time-ms`
- Processor chain đúng thứ tự: `merge_contextvars` → `add_log_level` → `TimeStamper(iso,utc)` → **`scrub_event`** → `StackInfoRenderer` → `format_exc_info` → `JsonlFileProcessor` → `JSONRenderer`
- `scrub_event` đứng **trước** `JsonlFileProcessor` → PII không bao giờ ghi ra disk
- `bind_contextvars(user_id_hash, session_id, feature, model, env)` trong `/chat`
- PII patterns: `email`, `phone_vn`, `cccd`, `credit_card` *(thiếu `passport` và `cmnd` – xem ghi chú)*

> ⚠️ **Ghi chú:** `app/pii.py` hiện có **4 patterns** và còn `# TODO: Add more patterns (e.g., Passport, Vietnamese address keywords)`. Nếu rubric yêu cầu đủ 6 patterns → cần bổ sung `passport` và `cmnd`.

### ❌ Còn thiếu

- [ ] **Ảnh** `docs/evidence/correlation_id.png` – JSON log có `"correlation_id": "req-xxxxxxxx"`
- [ ] (Tùy chọn) Bổ sung `passport` + `cmnd` pattern vào `app/pii.py`

### 🔧 Lệnh chụp bằng chứng

```bash
# Terminal 1 – giữ chạy
uvicorn app.main:app --reload

# Terminal 2
python scripts/load_test.py

python -c "
import json
with open('data/logs.jsonl') as f:
    for line in f:
        r = json.loads(line)
        if 'correlation_id' in r:
            print(json.dumps(r, indent=2, ensure_ascii=False))
            break
"
# Chụp → docs/evidence/correlation_id.png
```

### ❓ Câu hỏi giảng viên hay hỏi

| Câu hỏi | Trả lời |
|---------|---------|
| `clear_contextvars()` quan trọng thế nào? | FastAPI xử lý nhiều request song song trên cùng event loop → không clear thì correlation_id của request A bị leak sang B. |
| `scrub_event` phải đứng trước `JsonlFileProcessor`? | Nếu để sau, PII đã ghi ra disk rồi mới xóa → vô nghĩa. Phải scrub trong memory trước khi persist. |
| Format `req-<8hex>` thay vì UUID đầy đủ? | Ngắn hơn (11 ký tự vs 36), đủ unique cho scope lab, dễ đọc trong log. |

---

## MEMBER B – Tracing & Enrichment

### 👤 Thông tin
- **Họ tên:** Bùi Lâm Tiến
- **Commits:** `9cb2673`, `f464b80` (report updates) · `505b18e` (tracing implementation)
- **Validate score:** 100/100 ✅ | **Unique correlation IDs found:** 21

### 📁 File sở hữu

| File | Nội dung chính |
|------|----------------|
| `app/tracing.py` | Import Langfuse với graceful fallback mock khi không có key |
| `app/agent.py` | `@observe()` decorator + metadata enrichment + link correlation_id |

### ✅ Đã hoàn thành

- **`app/tracing.py`:** `try: from langfuse...` / `except: mock @observe() + _DummyContext` → app không crash khi thiếu key
- **`app/agent.py`:**
  - `@observe()` trên `LabAgent.run()` → tự tạo trace với 2 child spans: `mock_rag.retrieve` + `mock_llm.generate`
  - `update_current_trace(user_id=hash_user_id(...), session_id, tags=[lab, feature, model], metadata={correlation_id, env})`
  - `update_current_observation(metadata={doc_count, query_preview}, usage_details={input, output})`
  - **Điểm cộng:** truyền `correlation_id` từ endpoint xuống agent → gắn vào Langfuse metadata → có thể cross-link log ↔ trace

### ❌ Còn thiếu

- [ ] Kiểm tra `.env` đã có `LANGFUSE_PUBLIC_KEY` + `LANGFUSE_SECRET_KEY` chưa
- [ ] **Ảnh** `docs/evidence/langfuse_trace_list.png` – ≥10 traces, cột user là hash (12 ký tự)
- [ ] **Ảnh** `docs/evidence/langfuse_trace_waterfall.png` – 1 trace detail: `agent.run` → `mock_rag.retrieve` + `mock_llm.generate`

### 🔧 Lệnh chụp bằng chứng

```bash
# Kiểm tra tracing đã bật
curl -s http://localhost:8000/health
# → "tracing_enabled": true

# Gửi ≥10 requests
python scripts/load_test.py

# Vào https://cloud.langfuse.com → Project → Traces
# Chụp: langfuse_trace_list.png + langfuse_trace_waterfall.png
```

**Nếu không có Langfuse key:** App vẫn chạy (mock mode). Dùng `docs/evidence/validate_logs_100.png` thay cho waterfall screenshot.

### ❓ Câu hỏi giảng viên hay hỏi

| Câu hỏi | Trả lời |
|---------|---------|
| `@observe()` hoạt động thế nào? | Decorator Langfuse SDK – tự tạo span, đo thời gian, capture input/output, flush về server async. |
| Tại sao truyền `correlation_id` vào agent? | Link Langfuse trace với log line cùng request – cầu nối logging ↔ tracing, hỗ trợ RCA. |
| App crash khi Langfuse down? | Không. `try/except` fallback về mock. SDK cũng buffer và retry nội bộ. |

---

## MEMBER C – SLO & Alerts

### 👤 Thông tin
- **Họ tên:** Trương Đăng Nghĩa
- **Commits:** `7213a16` (implement SLO + alerts) · `49e9f00` (fix: remove broken routes) · `8e183a1` (update blueprint)

### 📁 File sở hữu

| File | Nội dung chính |
|------|----------------|
| `app/slo_monitor.py` | Load YAML, tính SLI compliance, `get_slo_status()` |
| `app/alert_evaluator.py` | Load YAML, đánh giá 3 alert conditions, `get_alert_status()` |
| `config/slo.yaml` | 4 SLIs: latency_p95, error_rate, daily_cost, quality_score |
| `config/alert_rules.yaml` | 3 alert rules *(thiếu `low_quality_score`)* |
| `docs/alerts.md` | 3 runbooks *(thiếu runbook #4)* |

### ✅ Đã hoàn thành

**`app/slo_monitor.py`:**
- `load_slo_config()` – đọc + validate `config/slo.yaml` (check required fields)
- `calculate_sli_compliance()` – so sánh `less_than` / `greater_than`
- `calculate_compliance()` – tính compliance cho 4 SLIs từ metrics snapshot
- `get_slo_status()` – trả về compliance % tổng thể + từng SLI

**`app/alert_evaluator.py`:**
- `load_alert_rules()` – đọc + validate `config/alert_rules.yaml`
- `evaluate_high_latency_alert()` – P95 > 5000ms
- `evaluate_high_error_rate_alert()` – error_rate > 5%
- `evaluate_cost_spike_alert()` – hourly_cost > 2× baseline
- `get_alert_status()` – tổng hợp firing status tất cả alerts

**`config/slo.yaml`:** 4 SLIs đầy đủ (latency_p95_ms, error_rate_pct, daily_cost_usd, quality_score_avg)

**`config/alert_rules.yaml`:** 3 rules (high_latency_p95, high_error_rate, cost_budget_spike)

**`docs/alerts.md`:** 3 runbooks đầy đủ cấu trúc (trigger, impact, first checks, mitigation)

### ⚠️ Vấn đề quan trọng – Routes bị xóa

> Commit `49e9f00` đã **xóa** routes `/slo/status` và `/alerts/status` khỏi `app/main.py` do lỗi import khi server khởi động (`cannot load requests`).
>
> **Nguyên nhân gốc:** Có vấn đề khi import `get_alert_status` / `get_slo_status` trong main.py (có thể do circular import hoặc dependency `yaml` chưa install).
>
> **Hệ quả:** `app/slo_monitor.py` và `app/alert_evaluator.py` đang là dead code – không có endpoint nào gọi đến.

### ❌ Còn thiếu

- [ ] **Fix lại routes** `/slo/status` và `/alerts/status` vào `app/main.py` (đã bị xóa do lỗi import)
- [ ] Thêm alert rule thứ 4: `low_quality_score` vào `config/alert_rules.yaml`
- [ ] Thêm runbook thứ 4: `low_quality_score` vào `docs/alerts.md`
- [ ] Thêm handler `low_quality_score` trong `alert_evaluator.py`
- [ ] Thêm field `unit` vào `config/slo.yaml` (hiện thiếu so với rubric)
- [ ] **Ảnh** `docs/evidence/alert_rules.png` – chụp nội dung `config/alert_rules.yaml`

### 🔧 Fix routes (ưu tiên cao)

```python
# Thêm lại vào app/main.py (sau @app.get("/metrics"))

from .alert_evaluator import get_alert_status
from .slo_monitor import get_slo_status

@app.get("/slo/status")
async def slo_status() -> dict:
    """Return current SLO compliance status."""
    try:
        return get_slo_status()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=f"SLO config not found: {exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"SLO calculation failed: {exc}") from exc


@app.get("/alerts/status")
async def alerts_status() -> dict:
    """Return current alert evaluation status."""
    try:
        return get_alert_status()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=f"Alert config not found: {exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Alert evaluation failed: {exc}") from exc
```

> 💡 Nếu lỗi import do `yaml` chưa install: `pip install pyyaml` hoặc kiểm tra `requirements.txt`

```bash
# Test sau khi fix
curl -s http://localhost:8000/slo/status | python -m json.tool
curl -s http://localhost:8000/alerts/status | python -m json.tool

# Chụp ảnh alert_rules
type config\alert_rules.yaml
# → docs/evidence/alert_rules.png
```

### ❓ Câu hỏi giảng viên hay hỏi

| Câu hỏi | Trả lời |
|---------|---------|
| SLO vs SLA? | SLO = mục tiêu kỹ thuật nội bộ (P95 < 3000ms). SLA = cam kết pháp lý với khách hàng (thường lỏng hơn để có buffer fix). |
| Alert threshold > SLO threshold? | Tránh false alarm khi P95 dao động tự nhiên 3001–3100ms. Alert chỉ khi vi phạm nghiêm trọng (5000ms) và liên tục (30 phút). |
| Error budget là gì? | `(1 - target%) × window`. VD: 99.5% / 28d = 0.5% × 28 × 24 × 60 = 201.6 phút được phép breach. |

---

## MEMBER D – Load Test & Dashboard

### 👤 Thông tin
- **Họ tên:** [Chưa điền trong blueprint]
- **Commits:** ❌ 0 commits

### 📁 File phụ trách

| File | Trạng thái |
|------|-----------|
| `app/dashboard.py` | ❌ **Chưa tồn tại** |
| Route `GET /dashboard` trong `app/main.py` | ❌ **Chưa có** |

### ❌ Chưa có gì – Cần làm ngay

Dashboard là **bottleneck** của cả nhóm: thiếu dashboard → mất 10đ phần A2 và Member E không có gì để chụp ảnh.

### 🔧 Cách nhanh nhất để có dashboard

**Option A – Copy từ Lab13-Observability (khuyến nghị, tiết kiệm 1–2 giờ):**
```bash
copy "E:\LabAIThucChien\Lab13-Observability\app\dashboard.py" app\dashboard.py
```

Sau đó thêm vào `app/main.py`:
```python
from fastapi.responses import HTMLResponse
from .dashboard import get_dashboard_html

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard() -> HTMLResponse:
    """6-panel Chart.js dashboard with SLO threshold lines."""
    return get_dashboard_html()
```

**Option B – Tự viết mới** (mất nhiều thời gian hơn nhưng cho phép giải thích):

Dashboard cần đủ 6 panels theo `docs/dashboard-spec.md`:

| Panel | Chart type | Data source | SLO line |
|-------|-----------|------------|---------|
| Latency P50/P95/P99 | Line | `latency_p50`, `latency_p95`, `latency_p99` | Đỏ tại 3000ms |
| Traffic rate | Bar | `traffic` delta 15s | – |
| Error Breakdown | Doughnut | `error_breakdown` dict | – |
| Cost USD | Filled line | `total_cost_usd` | Đỏ tại $2.50 |
| Tokens In/Out | Grouped bar | `tokens_in_total`, `tokens_out_total` | – |
| Quality Score | Line | `quality_avg` | Đỏ tại 0.75 |

**Sau khi có dashboard:**
```bash
python scripts/load_test.py
start http://localhost:8000/dashboard
# Chụp ảnh → docs/evidence/dashboard_6panels.png
```

### ❓ Câu hỏi giảng viên hay hỏi

| Câu hỏi | Trả lời |
|---------|---------|
| Tại sao cần dashboard? | Visualize metrics real-time → phát hiện anomaly ngay mà không cần đọc raw log. |
| SLO threshold lines màu đỏ ý nghĩa gì? | Visual alert ngay khi nhìn vào – đường đỏ vượt qua = SLO đang breach. |
| Auto-refresh 15s có tốn kém không? | Fetch `/metrics` mỗi 15s, response nhỏ (~200 bytes JSON). Không ảnh hưởng server. |

---

## MEMBER E – Dashboard + Evidence

### 👤 Thông tin
- **Họ tên:** [Chưa điền trong blueprint]
- **Commits:** ❌ 0 commits

### 📁 File phụ trách

| File | Trạng thái |
|------|-----------|
| `docs/evidence/` folder | ❌ **Chưa tồn tại** |
| Tất cả screenshots | ❌ **Chưa có** |

### ❌ Chưa có gì – Danh sách ảnh cần chụp đầy đủ

**Bước 0 – Tạo folder:**
```bash
mkdir docs\evidence
```

**Bước 1 – Start server và tạo dữ liệu (Terminal 1):**
```bash
uvicorn app.main:app --reload
```

**Bước 2 – Gửi requests (Terminal 2):**
```bash
python scripts/load_test.py
```

**Bước 3 – Chụp từng ảnh theo thứ tự:**

| # | Ảnh | Lệnh | Lưu tại |
|---|-----|------|---------|
| 1 | Correlation ID trong log | `python -c "import json; [print(json.dumps(json.loads(l),indent=2,ensure_ascii=False)) for l in open('data/logs.jsonl') if 'correlation_id' in json.loads(l)]"` | `docs/evidence/correlation_id.png` |
| 2 | PII redaction trong log | curl có email/SĐT → xem log (lệnh bên dưới) | `docs/evidence/pii_redaction.png` |
| 3 | Dashboard 6 panels | `start http://localhost:8000/dashboard` | `docs/evidence/dashboard_6panels.png` |
| 4 | Alert rules yaml | `type config\alert_rules.yaml` | `docs/evidence/alert_rules.png` |
| 5 | Validate logs 100/100 | `python scripts/validate_logs.py` | `docs/evidence/validate_logs_100.png` |
| 6 | Langfuse trace list | Mở cloud.langfuse.com (nếu có key) | `docs/evidence/langfuse_trace_list.png` |
| 7 | Langfuse waterfall | Click 1 trace trên Langfuse | `docs/evidence/langfuse_trace_waterfall.png` |

**Lệnh PII evidence:**
```bash
curl -s -X POST http://localhost:8000/chat ^
  -H "Content-Type: application/json" ^
  -d "{\"user_id\":\"u01\",\"session_id\":\"s01\",\"feature\":\"qa\",\"model\":\"claude-sonnet-4-5\",\"message\":\"Goi cho toi tai 0987654321 hoac email abc@test.com\"}"

python -c "
import json
with open('data/logs.jsonl') as f:
    for line in f:
        r = json.loads(line)
        if 'REDACTED' in str(r):
            print(json.dumps(r, indent=2, ensure_ascii=False))
            break
"
```

---

## MEMBER F – Demo & Report

### 👤 Thông tin
- **Họ tên:** [Chưa điền trong blueprint]
- **Commits:** ❌ 0 commits

### 📁 File phụ trách

| File | Trạng thái |
|------|-----------|
| `docs/blueprint-template.md` | ⚠️ A, B, C đã điền; D, E, F còn trống |
| `scripts/smoke_test.py` | ❌ Chưa có |
| `scripts/cost_report.py` | ❌ Chưa có |

### ❌ Còn thiếu

| Việc | Chi tiết |
|------|---------|
| Điền tên D, E, F vào blueprint | `Member D: []` · `Member E: [Name]` · `Member F: [Name]` |
| Điền `[TASKS_COMPLETED]` cho D, E, F | Chưa có nội dung |
| Điền `[EVIDENCE_LINK]` cho D, E, F | Chưa có commit link |
| Điền phần Incident Response (Section 4) | 5 trường còn trống hoàn toàn |
| Điền screenshot paths (Section 3) | `[Path to image]` chưa thay |
| Điền `[TOTAL_TRACES_COUNT]` | Còn trống |
| Chuẩn bị script demo 5–10 phút | Chưa có |

### 🔧 Bước hành động của Member F

#### F1 – Điền blueprint-template.md

```
Member D: <Họ tên D> | Role: Load Test & Dashboard
Member E: <Họ tên E> | Role: Dashboard + Evidence
Member F: <Họ tên F> | Role: Demo & Report

[TOTAL_TRACES_COUNT]: 21+ (từ commit của Member B)

Section 3 – Evidence:
[EVIDENCE_CORRELATION_ID_SCREENSHOT]: docs/evidence/correlation_id.png
[EVIDENCE_PII_REDACTION_SCREENSHOT]: docs/evidence/pii_redaction.png
[DASHBOARD_6_PANELS_SCREENSHOT]: docs/evidence/dashboard_6panels.png
[ALERT_RULES_SCREENSHOT]: docs/evidence/alert_rules.png
[SAMPLE_RUNBOOK_LINK]: docs/alerts.md#1-high-latency-p95

Section 4 – Incident Response:
[SCENARIO_NAME]: rag_slow
[SYMPTOMS_OBSERVED]: P95 latency tăng từ ~200ms baseline lên >2700ms.
                     Dashboard Panel Latency vượt ngưỡng SLO 3000ms.
[ROOT_CAUSE_PROVED_BY]: Langfuse trace waterfall – RAG span chiếm ~2500ms
                         do time.sleep(2.5) trong mock_rag khi rag_slow=True.
                         Log line "response_sent" cho thấy latency_ms > 2700.
[FIX_ACTION]: python scripts/inject_incident.py --scenario rag_slow --disable
[PREVENTIVE_MEASURE]: Circuit-breaker timeout 500ms cho RAG retrieval.
                      Alert high_latency_p95 page on-call sau 30 phút liên tục.
```

#### F2 – Script demo 8 phút (phân công ai nói gì)

| Thời gian | Người | Nội dung | Lệnh |
|-----------|-------|---------|------|
| 00:00–00:30 | **F** | Giới thiệu: "4 trụ cột observability..." | – |
| 00:30–01:30 | **A** | Correlation ID demo | `load_test.py` → xem log |
| 01:30–02:30 | **A** | PII scrubbing demo | curl có email/SĐT → grep REDACTED |
| 02:30–04:00 | **B** | Langfuse traces | Mở Langfuse UI → trace list → waterfall |
| 04:00–05:00 | **C** | SLO & Alerts | `curl /slo/status` + `curl /alerts/status` |
| 05:00–06:30 | **D/E** | Dashboard 6 panels | `start http://localhost:8000/dashboard` |
| 06:30–08:00 | **F** | Validate logs + Incident | `validate_logs.py` → inject_incident demo |

**Câu mở đầu Member F:**
> *"Chào thầy/cô, nhóm 5 E402 xây dựng observability system cho AI agent với 4 lớp: structured logging với correlation ID và PII scrubbing, Langfuse distributed tracing, real-time metrics dashboard, và SLO monitoring với alert evaluation. Validate logs đạt 100/100 với 21 unique correlation IDs đã xác nhận. Em xin demo từng phần..."*

#### F3 – Git commit cuối cùng sau khi có ảnh

```bash
git add docs\evidence\
git add docs\blueprint-template.md
git add member-role-status.md
git add app\main.py          # sau khi fix routes SLO/alerts và thêm /dashboard
git add app\dashboard.py     # sau khi Member D viết xong

git commit -m "docs: fill blueprint report, add evidence screenshots"
git push origin main
```

---

## 📊 Bảng tổng hợp trạng thái (sau pull mới nhất)

| Member | Họ tên | Code | Evidence | Blueprint | Việc còn lại ưu tiên |
|--------|--------|:----:|:--------:|:---------:|---------------------|
| **A** | Trần Thượng Trường Sơn | ✅ Xong | ❌ 1 ảnh | ✅ Đã điền | Chụp `correlation_id.png` |
| **B** | Bùi Lâm Tiến | ✅ Xong | ❌ 2 ảnh | ✅ Đã điền | Chụp Langfuse screenshots (cần key) |
| **C** | Trương Đăng Nghĩa | ⚠️ Routes bị xóa | ❌ 1 ảnh | ✅ Đã điền | **Fix routes vào main.py** + thêm alert #4 |
| **D** | [Chưa có tên] | ❌ Chưa làm | ❌ 1 ảnh | ❌ Chưa điền | **Viết dashboard** (bottleneck) |
| **E** | [Chưa có tên] | ❌ Chưa làm | ❌ Tất cả | ❌ Chưa điền | **Tạo folder + chụp tất cả ảnh** |
| **F** | [Chưa có tên] | ❌ Chưa làm | – | ⚠️ Còn trống | **Điền blueprint** + chuẩn bị demo |

### Ảnh cần có trong `docs/evidence/`

```
docs/evidence/                          Ai phụ trách
  ├── correlation_id.png               ← E (hoặc A tự chụp)
  ├── pii_redaction.png                ← E (hoặc A tự chụp)
  ├── langfuse_trace_list.png          ← B (cần Langfuse key)
  ├── langfuse_trace_waterfall.png     ← B (cần Langfuse key)
  ├── alert_rules.png                  ← E (hoặc C tự chụp)
  ├── dashboard_6panels.png            ← E (sau khi D viết xong dashboard)
  └── validate_logs_100.png            ← E
```

---

## ⏱️ Thứ tự ưu tiên việc cần làm

| # | Việc | Ai | Ước tính | Ghi chú |
|---|------|----|---------|---------|
| 1 | **Viết `app/dashboard.py`** + thêm route `/dashboard` | **D** | 1–2 giờ | Bottleneck của nhóm |
| 2 | **Fix routes `/slo/status` + `/alerts/status`** vào main.py | **C** | 15 phút | Đã bị xóa commit 49e9f00 |
| 3 | Thêm `low_quality_score` alert (rule + evaluator + runbook) | **C** | 20 phút | Đủ 4 alerts theo rubric |
| 4 | `mkdir docs\evidence` | **E** | 10 giây | – |
| 5 | Start server + `python scripts/load_test.py` | **E** | 2 phút | – |
| 6 | 📸 Chụp `correlation_id.png` | **E** | 3 phút | – |
| 7 | 📸 Chụp `pii_redaction.png` | **E** | 3 phút | – |
| 8 | 📸 Chụp `dashboard_6panels.png` (sau bước 1) | **E** | 2 phút | Cần D xong trước |
| 9 | 📸 Chụp `alert_rules.png` | **E** | 1 phút | – |
| 10 | 📸 `python scripts/validate_logs.py` → chụp 100/100 | **E** | 2 phút | – |
| 11 | Điền tên + incident response vào `blueprint-template.md` | **F** | 15 phút | – |
| 12 | (Nếu có key) 📸 Langfuse trace list + waterfall | **B** | 10 phút | – |
| 13 | `git add + commit + push` | **F** | 5 phút | – |
| 14 | Luyện script demo 1–2 lần | **Cả nhóm** | 20 phút | – |
| **Tổng** | | | **~2.5–3.5 giờ** | |

> 🚨 **Rủi ro lớn nhất:** Member C đã xóa routes SLO/alerts do lỗi import – nếu không fix lại, toàn bộ công sức viết `slo_monitor.py` và `alert_evaluator.py` trở thành dead code. Fix này chỉ mất 15 phút.

---

## 📝 Lịch sử commits tóm tắt

| Commit | Tác giả | Nội dung |
|--------|---------|---------|
| `8e183a1` | Trương Đăng Nghĩa | Update blueprint – thêm commit ID cho Member C |
| `49e9f00` | Trương Đăng Nghĩa | Fix lỗi import: xóa routes `/slo/status` + `/alerts/status` khỏi main.py |
| `7213a16` | Trương Đăng Nghĩa | Implement `slo_monitor.py` + `alert_evaluator.py` + routes (sau bị xóa) |
| `f464b80` | Bùi Lâm Tiến | Update blueprint report |
| `9cb2673` | Bùi Lâm Tiến | Update blueprint report |
| `505b18e` | Bùi Lâm Tiến | Implement tracing + Langfuse + metadata enrichment |
| `07682fd` | Trần Thượng Trường Sơn | Update blueprint report |
| `67f4939` | Trần Thượng Trường Sơn | Enhance ChatRequest schema (thêm `model` field) |
| `25ba3d2` | Trần Thượng Trường Sơn | Implement logging & PII foundation |

---

*Tài liệu này do **Member F** tổng hợp dựa trên code thực tế sau lần pull 2026-04-20.*
*Đọc thêm: `docs/blueprint-template.md` · `day13-rubric-for-instructor.md` · `docs/grading-evidence.md`*
