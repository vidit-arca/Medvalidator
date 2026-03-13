# Medical Bill Validation Engine

A robust, auditable, and regulator-safe price validation & fraud detection engine for hospital bills. This system uses a hybrid trusted architecture with local LLMs (Mistral 7B) and deterministic validation against a Master Price Database.

## Features

*   **Ingestion**: Accepts bill images/PDFs via API.
*   **OCR**: Extracts text using `unstructured` (open-source).
*   **LLM Mapping**: Maps messy OCR text to standard procedure codes using a local Mistral 7B model (via Ollama).
*   **Deterministic Validation**: Compares extracted prices against a Master Price Database with configurable tolerance.
*   **Audit Logging**: Immutable, tamper-proof logs for all decisions.
*   **Master Price Management**: API to manage standard procedure prices.

## Prerequisites

1.  **Python 3.10+**
2.  **Ollama**: Installed and running with `mistral` model.
    *   Install Ollama: [https://ollama.com](https://ollama.com)
    *   Pull model: `ollama pull mistral`

## Installation

1.  **Clone the repository** (if applicable) or navigate to the project directory.

2.  **Create a virtual environment**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Initialize Database**:
    The database is SQLite (`medical_bills.db`). It has been pre-populated with the Master Price CSV.
    If you need to re-import data:
    ```bash
    # Ensure venv is active
    python import_csv.py
    ```

## Running the Application

1.  **Start the FastAPI server**:
    ```bash
    # Ensure venv is active
    uvicorn app.main:app --reload
    ```
    The API will be available at `http://localhost:8000`.

2.  **Access API Documentation**:
    Open your browser and navigate to `http://localhost:8000/docs` to see the Swagger UI.

## Usage Guide

### 1. Upload a Bill
Use the `/api/v1/upload` endpoint to upload a bill (PDF or Image).
```bash
curl -X POST -F "file=@/path/to/bill.pdf" http://localhost:8000/api/v1/upload
```
Response will contain a `bill_id`.

### 2. Check Status
Use the `/api/v1/bills/{bill_id}` endpoint to check the processing status and final decision.

### 3. Manage Master Prices
Use the `/api/v1/master-prices` endpoints to list, add, or view standard prices.

## Verification

To run a system verification test (mocking OCR and LLM):
```bash
python verify_system.py
```

## Project Structure

*   `app/api`: API endpoints (Ingestion, Master Price).
*   `app/services`: Core logic (OCR, LLM, Validator, Audit, Orchestrator).
*   `app/models.py`: Database models (SQLModel).
*   `app/core`: Configuration and Database setup.
*   `raw_storage`: Directory where uploaded files are saved.
