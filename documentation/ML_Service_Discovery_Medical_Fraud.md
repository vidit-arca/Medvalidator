# ML Pipeline Current Status — Discovery Questionnaire

> Use this as a guideline and target state. Provide whatever is currently available, note gaps or challenges, and we can work through the remaining items iteratively. End goal: each service independently deployable, stateless where possible, with clearly defined input/output contracts.

**Services to document:**
| # | Service | Status |
|---|---------|--------|
| 1 | Medical Bill Validator | Available |
| 2 | Bill Fraud Detection System | Available |

---

## 1. Service Architecture & Deployment

### Medical Bill Validator
- **Packaging:** Docker Image (FastAPI backend)
- **Compute:** 
  - **API:** Standard CPU/RAM
  - **LLM/Inference:** External Ollama instance (requires GPU on the external host `192.168.112.2:11434`)
- **Stateless:** No — State is stored in a PostgreSQL database and uploaded files are saved to a local `raw_storage` directory.
- **Health endpoint:** Yes (`/health`)
- **Current deployment:** Docker Compose (includes Backend, Frontend, Postgres, and Redis containers)
- **Target model:** Standalone

### Bill Fraud Detection System
- **Packaging:** Docker Image (FastAPI)
- **Compute:** 
  - CPU/RAM for API and scikit-learn anomaly detection
  - `efficientnet_b0` feature extractor (can utilize GPU if available, otherwise CPU)
- **Stateless:** Yes — Uploaded images are temporary (only the last 20 are kept for debugging in the `uploads/` folder).
- **Health endpoint:** No explicit `/health`, but `/api/models` acts as a status check.
- **Current deployment:** Docker Compose (`bill-fraud-system-api` container)
- **Target model:** Standalone

---

## 2. API Contracts — Input & Output

### Medical Bill Validator
- **Endpoint(s):** 
  - `POST /api/v1/upload` — Sync upload, triggers async background processing
  - `GET /api/v1/bills/{bill_id}` — Sync fetch for results
  - `POST /api/v1/master-prices` — Sync master price CRUD
- **Request schema (`POST /api/v1/upload`):**
  ```http
  POST /api/v1/upload
  Content-Type: multipart/form-data

  --boundary
  Content-Disposition: form-data; name="file"; filename="bill.pdf"
  ```
  | Field | Type | Required | Description |
  |-------|------|----------|-------------|
  | `file` | file | Yes | Document to upload and process |
- **Response schema (`POST /api/v1/upload`):**
  ```json
  {
    "id": "uuid-1234",
    "filename": "bill.pdf",
    "status": "pending",
    "upload_timestamp": "2026-07-01T00:00:00"
  }
  ```
- **Authentication:** None (currently allows `*` origins for development)
- **Error handling:** HTTP 400 (Invalid format), 404 (Not found)
- **Timeouts:** Immediate HTTP 202-like response; processing occurs asynchronously via FastAPI `BackgroundTasks`.

### Bill Fraud Detection System
- **Endpoint(s):** `POST /api/analyze` — Sync processing
- **Request schema:**
  ```http
  POST /api/analyze
  Content-Type: multipart/form-data

  --boundary
  Content-Disposition: form-data; name="file"; filename="document.pdf"
  Content-Disposition: form-data; name="doc_type"
  
  bill
  --boundary--
  ```
  | Field | Type | Required | Description |
  |-------|------|----------|-------------|
  | `file` | file (PDF/Image) | Yes | Document to analyze |
  | `doc_type`| string | No | Either `bill` or `card` (defaults to `bill`) |
- **Response schema:**
  ```json
  {
    "status": "TAMPERED",
    "confidence": 99.9,
    "combined_score": 3.1415,
    "deep_score": 0.8,
    "forensic_score": 0.7,
    "threshold": 2.0,
    "processing_time": 1.25,
    "doc_type": "bill",
    "model_name": "Bill / Prescription",
    "image_info": {
      "filename": "document.pdf",
      "width": 1024,
      "height": 768,
      "format": "JPG"
    },
    "upload_url": "/uploads/upload_123.jpg",
    "tamper_reason": "Visual/structural anomalies detected"
  }
  ```
- **Authentication:** None
- **Error handling:** HTTP 400 (Unknown doc type, PDF conversion failed), HTTP 500 (Internal processing failure)
- **Timeouts:** Sync processing, latency scales with image size (typically under a few seconds).

---

## 3. Pipeline — End-to-End Data Flow

### Medical Bill Validator Data Flow
- **Pipeline stages:**
  1. Frontend uploads file via `/api/v1/upload`.
  2. File is saved to the host-mounted `raw_storage` directory. A database record is created in PostgreSQL with `status: PENDING`.
  3. A background task (`orchestrator.process_bill`) is triggered.
  4. The Orchestrator currently interacts with the Landing API for OCR (which will be replaced with an in-house OCR built by Vidit) and the external Ollama LLM to extract line items and mapped procedure codes.
  5. Extracted codes are matched against the `master_price` table to determine `is_payable` and compute `price_difference`.
  6. The frontend continuously polls `/api/v1/bills/{bill_id}` for the final processed data.
- **Output:** Stored directly into the PostgreSQL database (Line Items, Audits, Status updates).

### Bill Fraud Detection Data Flow
- **Pipeline stages:**
  1. Frontend uploads a document via `/api/analyze`.
  2. If the document is a PDF, it is converted to JPEG via `sips` (macOS) or `pdf2image`.
  3. The image is passed through `FeatureExtractor` (EfficientNet B0) for structural anomalies and `ForensicFeatureExtractor` for Error Level Analysis (ELA).
  4. Features are scored against pre-trained Pickle models (`bill_model_v2.pkl` or `card_model.pkl`).
  5. ELA and Deep scoring logic determines if the image is `TAMPERED` or `GENUINE`.
- **Output:** Sync HTTP JSON response returned directly to the client. No permanent database state is altered.

---

## 4. Batch vs Real-Time Processing

### Medical Bill Validator
- **Mode:** **Batch / Async Polling**
- **Architecture:** API returns a job ID immediately. The system processes one document at a time in the background. The client must poll the database to retrieve results.

### Bill Fraud Detection System
- **Mode:** **Real-Time**
- **Architecture:** API blocks and processes the image synchronously inline, returning the classification payload directly in the HTTP response.

---

## 5. Multi-Tenant Design Inputs (NOT IMPLEMENTED)

- **`tenant_id` in request:** No
- **Model isolation:** Models are shared globally across all requests.
- **Insight tagging:** None. Fraud detection insights are ephemeral, and medical bill insights are associated with a generated `bill_id` UUID without tenant scoping.

---

## 6. Data Ingestion — Current Format

- **Input data format:** PDF, JPEG, PNG
- **Preprocessing Details:**
  - **Medical Bill Validator:** Saves raw files to disk. Text extraction/OCR currently uses the Landing API (to be replaced with an in-house OCR built by Vidit) before the parsed text is sent to LLM endpoints.
  - **Bill Fraud Detection:** Strictly converts PDFs into flat JPEGs before performing image analysis and feature extraction. Cannot process multi-page PDFs simultaneously (only evaluates the first page converted).

---

## 7. Model Management (NOT IMPLEMENTED)

| Aspect | Medical Bill Validator | Bill Fraud Detection |
|--------|:---:|:---:|
| Model registry? | No (External Ollama) | No (Local `.pkl` files) |
| A/B testing? | No | No |
| Retraining frequency | N/A | Manual / Offline |
| Version-agnostic endpoint? | Yes | Yes (Abstracted via `doc_type`) |
| Base model / LLM used | External LLM | EfficientNet_B0 + IsolationForest |

---

## 8. Logging, Monitoring & Resilience (NOT IMPLEMENTED)

| Aspect | Medical Bill Validator | Bill Fraud Detection |
|--------|:---:|:---:|
| request_id logged | No | No |
| Latency tracked | No | Yes (returned in HTTP response payload) |
| Model version logged | No | Yes (returned in HTTP response payload) |
| Confidence logged | N/A | Yes |
| Error details logged | Basic Exception prints | Stack traces printed to console |

- **Resilience:**
  - Medical Bill Validator: No DLQ (Dead Letter Queue) or fallback if Ollama LLM is down; the background task will fail and the bill might be stuck or marked as failed.
  - Fraud Detection: No circuit breakers; errors return a 500 status code directly to the user.
