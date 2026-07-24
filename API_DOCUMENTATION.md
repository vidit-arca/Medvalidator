# Medical Bill Validator API Documentation

## Overview
The Medical Bill Validator is a service designed to ingest, process, and validate medical bills. It uses OCR, LLM extraction, and a rules-based validation engine against a master price list to verify if the charges on a medical bill are accurate, payable, and within allowed variance limits.

This document details the available APIs, their purposes, and how integrators can use this service in their workflows.

## Base URL
All API endpoints are prefixed with `/api/v1` except for the root health check.
Example: `http://localhost:8000/api/v1`

---

## 1. Health Check

### `GET /health`
Checks if the API service is up and running.

**Response**
```json
{
  "status": "ok"
}
```

---

## 2. Ingestion & Bill Processing APIs

These APIs are used to upload medical bills and track their processing status.

### `POST /api/v1/upload`
Uploads a medical bill document (PDF, JPEG, PNG, etc.) to the system and triggers background processing. 

**Request**
- `Content-Type: multipart/form-data`
- `file`: The document to be uploaded.

**Response (BillSubmissionResponse)**
```json
{
  "id": "uuid",
  "filename": "bill.pdf",
  "upload_timestamp": "2023-10-12T10:00:00Z",
  "status": "PENDING",
  "final_decision": null
}
```
*Note:* The `status` field will update to `PROCESSING`, and then `COMPLETED` or `FAILED` as the background tasks finish.

### `GET /api/v1/bills`
Retrieves a list of all uploaded medical bills, ordered by the most recently uploaded.

**Response (List of BillSubmissionResponse)**
Returns an array of bill submission objects.

### `GET /api/v1/bills/{bill_id}`
Retrieves detailed information about a specific medical bill, including extracted line items, mapped procedure codes, validation decisions, and price differences.

**Path Parameters**
- `bill_id`: The UUID of the uploaded bill.

**Response (BillDetailResponse)**
```json
{
  "id": "uuid",
  "filename": "bill.pdf",
  "upload_timestamp": "2023-10-12T10:00:00Z",
  "status": "COMPLETED",
  "final_decision": "VALID",
  "line_items": [
    {
      "raw_ocr_text": "Chest X-Ray",
      "extracted_price": 55.00,
      "quantity": 1,
      "mapped_procedure_code": "XRAY_CHEST",
      "mapping_confidence": 0.95,
      "variance_percent": 10.0,
      "line_decision": "VALID",
      "is_payable": true,
      "price_difference": 5.00
    }
  ],
  "audit_logs": [
    {
      "timestamp": "2023-10-12T10:01:00Z",
      "component": "VALIDATOR",
      "input_data": "{...}",
      "output_data": "{...}"
    }
  ]
}
```

---

## 3. Master Price APIs

These APIs manage the master list of medical procedures and their standard prices, used by the validation engine to determine if billed amounts are acceptable.

### `POST /api/v1/master-prices`
Creates a new master price entry for a procedure.

**Request Body (JSON)**
```json
{
  "procedure_code": "XRAY_CHEST",
  "procedure_name": "Chest X-Ray",
  "cost": 40.00,
  "standard_unit_price": 50.00,
  "mrp": 50.00,
  "allowed_variance_percent": 10.0,
  "is_active": true,
  "is_payable": true
}
```

### `GET /api/v1/master-prices`
Retrieves all master price records.

**Response**
Returns an array of master price objects.

### `GET /api/v1/master-prices/{code}`
Retrieves the master price details for a specific procedure code.

**Path Parameters**
- `code`: The procedure code (e.g., `XRAY_CHEST`).

### `POST /api/v1/master-prices/seed`
Seeds the database with dummy master price data for testing purposes.

**Response**
```json
{
  "status": "seeded"
}
```

---

## How to Integrate

1. **Setup the Master Data**: Before validating bills, ensure your system has populated the Master Price list either by syncing your catalog via `POST /api/v1/master-prices` or for testing, using the `POST /api/v1/master-prices/seed` endpoint.
2. **Submit a Document**: Send the patient's medical bill via `POST /api/v1/upload`. Save the `id` returned in the response.
3. **Poll for Status**: Since processing runs in the background, poll `GET /api/v1/bills/{bill_id}` periodically until the `status` is `COMPLETED` or `FAILED`.
4. **Review the Results**: Once completed, inspect the `line_items` array in the `GET /api/v1/bills/{bill_id}` response. You can look at `line_decision`, `is_payable`, and `price_difference` to determine which charges should be approved or flagged for manual review.
