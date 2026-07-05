# System Requirements: Medical Bill Validator

This document outlines the system requirements and dependencies required to build, run, and develop the **Medical Bill Validator** application. 

The application utilizes a **FastAPI backend** (orchestrating OCR & local/remote deep learning parsing), a **Vite + React frontend**, a **PostgreSQL database**, and **Redis** for task tracking/caching.

---

## 1. Hardware Requirements

Running the full stack locally—especially when using a local LLM (`mistral`) via **Ollama**—is the primary driver for hardware resource requirements.

| Resource | Minimum Specification | Recommended Specification |
| :--- | :--- | :--- |
| **CPU** | Modern Multi-Core CPU (Intel Core i5/i7 10th Gen+, AMD Ryzen 5+, or **Apple Silicon M-Series**) | 8-Core+ Modern CPU (Apple Silicon M1/M2/M3/M4 or Intel/AMD equivalent) |
| **RAM** | **16 GB RAM** (If Ollama is run locally)<br>**8 GB RAM** (If Ollama runs on a remote server) | **16 GB - 32 GB RAM** (Unified memory on macOS or high-speed DDR4/DDR5) |
| **GPU** | CPU-Only (Ollama runs on CPU, but inference will take 1–2 minutes per bill) | **Dedicated GPU** with **8 GB+ VRAM** (NVIDIA RTX 3060/4060+ or **Apple Silicon Unified Memory**) |
| **Storage** | **10 GB** available SSD space | **20 GB+** available SSD space (for Docker images, DB data, and downloaded LLM weights) |

> [!NOTE]
> **Apple Silicon Macs (M1/M2/M3/M4)** are highly optimized for this stack because their **unified memory** allows the GPU to access the model weights directly, enabling fast LLM inference without needing an external GPU.

---

## 2. Software Prerequisites

You can run this application in two main ways: **via Docker Compose (highly recommended)** or **directly on your host machine (local development setup)**.

### Option A: Running via Docker (Recommended)
This is the simplest way to get the app running, as all package-level system dependencies (Tesseract, Poppler, etc.) are pre-packaged inside the containers.

* **Docker:** Docker Desktop v20.10+ (for macOS or Windows) or Docker Engine on Linux.
* **Docker Compose:** v2.x or higher (included in Docker Desktop).
* **Ollama:** Installed locally on your host machine (download from [ollama.com](https://ollama.com/)) with the `mistral` model downloaded:
  ```bash
  ollama pull mistral
  ```

---

### Option B: Running Locally (Bare Metal / Development)
If you prefer to run the backend and frontend directly in your native environment, you will need to install the following runtimes, databases, and system libraries:

#### Runtimes & Databases
* **Python:** `3.10` to `3.12`
* **Node.js:** `18.x` or `20.x` (with `npm`)
* **PostgreSQL:** Version `15` or `16`
* **Redis:** Version `7.x`

#### OS-Specific System Libraries (Required for local OCR & PDF processing)
These are mandatory because the Python backend uses `pytesseract` and `pdf2image` as its fallback OCR parser:

* **macOS (via Homebrew):**
  ```bash
  brew install tesseract poppler libmagic
  ```
* **Linux (Ubuntu/Debian):**
  ```bash
  sudo apt-get update
  sudo apt-get install -y tesseract-ocr poppler-utils libmagic1
  ```
* **Windows:**
  * Must manually download and install the **Tesseract OCR binary** and add it to your System environment variable `PATH`.
  * Must download **Poppler for Windows** and add its `bin/` directory to the system environment variable `PATH`.
  * *Note: Using WSL2 on Windows is highly recommended to simplify this setup.*

---

## 3. External API Configuration

* **LandingAI API Key:** The system is configured to use **Landing AI's Agentic Document Extraction API** (`https://api.va.landing.ai`) as its primary, high-accuracy OCR processor. 
  * Ensure your API key is set in your `.env` file under `LANDING_API_KEY`.
  * When this API is configured, the local CPU/GPU OCR processing overhead is minimized as the parsing runs in the cloud.
  * If this key is missing or disabled, the application falls back to **Tesseract** and **Unstructured**, which will run entirely locally on your machine.

---

## 4. Quick Verification Checklist

Before starting the containers, verify your host dependencies:
1. Docker Desktop is running.
2. Ollama is running in your background:
   * Test it by visiting: `http://localhost:11434`
   * Confirm the model is pulled by running: `ollama list` and verifying `mistral` is in the output list.
