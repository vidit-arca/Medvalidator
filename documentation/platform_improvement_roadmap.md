# Medical Bill Validator - Platform Improvement Roadmap

This document outlines strategic architectural and logical improvements to enhance the accuracy, scalability, and robustness of the Medical Bill Validator platform.

## 1. Upgrade the Mapping Engine (Semantic Search)
**Current State:** 
The orchestrator currently maps extracted items to the Master Database using deterministic rules (Exact Match, Substring Match) and basic NER. Medical data is notoriously messy (e.g., "Dytor 10 Tab" vs "DYTOR 10MG TABLET"). Substring matching frequently fails here, leading to many items being marked as "Unmapped".

**Proposed Architecture:** 
* Implement **Vector Embeddings (Semantic Search)**. Convert all `MasterPrice` procedure names into vector embeddings using a fast, local embedding model (like `all-MiniLM-L6-v2`).
* Store these embeddings in a vector database. Since the platform already supports PostgreSQL, the **`pgvector`** extension is the ideal choice.
* **Workflow:** When an item is extracted from a bill, embed its text and perform a cosine similarity search against the database. This approach catches typos, abbreviations, and differently ordered words with near 100% accuracy.

## 2. Bulletproof the LLM Extraction
**Current State:** 
The platform uses Ollama (Mistral 7B) and relies on prompt engineering to force it to output valid JSON. Smaller models can easily get confused by complex table structures, leading to broken JSON schemas, hallucinated text, and `JSONDecodeError`s.

**Proposed Architecture:**
* Implement structured output constraints using a library like **Instructor** or **Outlines** for Python.
* **Workflow:** These libraries interface directly with local LLMs and physically constrain the token generation process. The model is mathematically forced to output valid JSON that exactly matches predefined Pydantic schemas, eliminating parsing errors.

## 3. Asynchronous Task Queue (Celery / RQ)
**Current State:** 
While the architecture diagram mentions a "Task Queue", the OCR and LLM processing (which can take minutes per document) currently risks blocking web server resources if not isolated properly.

**Proposed Architecture:**
* Integrate a robust task queue like **Celery** or **RQ (Redis Queue)**. The project already utilizes a Redis container, making this a seamless integration.
* **Workflow:** 
  1. User uploads a bill.
  2. FastAPI immediately returns a `job_id` (HTTP 202 Accepted).
  3. A separate background worker picks up the job, communicates with Triton and Ollama, updates the PostgreSQL database, and finishes.
  4. The React frontend polls the `job_id` or listens via WebSockets for the completion event to update the UI.

## 4. Advanced Fraud & Anomaly Detection
**Current State:** 
The validator engine currently checks if `extracted_price > standard_price` based on an `allowed_variance_percent`.

**Proposed Architecture:**
Expand the deterministic rule engine to catch deeper anomalies and potential fraud:
* **Quantity Limits:** Check if the quantity of a drug or test exceeds standard clinical guidelines (e.g., billing for 50 Blood Tests in one day for a single patient).
* **Duplicate Billing:** Hash the extracted items and check the database to see if the exact same bill was submitted for the same patient in the last 30 days.
* **Mutually Exclusive Procedures:** Implement a ruleset to flag bills that contain procedures that cannot logically or physically be performed together on the same day.

## 5. Multimodal Vision-Language Models (VLM)
**Current State:** 
The platform uses a disjointed two-step pipeline: Marker OCR (Triton) converts the image to Text/Markdown -> LLM (Mistral) parses the text. This pipeline is slow and prone to text alignment and hallucination issues during the OCR phase.

**Proposed Architecture:** 
* Replace the two-step Marker OCR and Mistral pipeline with a single local Vision-Language Model (VLM) like **LLaVA**, **Qwen-VL**, or **Pixtral**.
* **Workflow:** Pass the raw PDF image straight to the VLM with a prompt to "Extract the table as JSON". This allows the AI to visually "see" the table boundaries and formatting directly, skipping the lossy Markdown conversion step entirely and resulting in significantly higher accuracy and speed.
