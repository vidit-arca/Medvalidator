import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.ocr import ocr_service
from app.services.llm import llm_service

async def test_full_pipeline():
    file_path = "/Users/apple/Desktop/Medical-bills/data/34958501_S_MEDICINEBILL_page1_page_1.jpg"
    print(f"Testing on file: {file_path}")
    
    # 1. OCR Extraction using unstructured/tesseract
    print("Running Unstructured/Tesseract OCR...")
    raw_text = ocr_service.extract_text(file_path)
    print("\n--- Raw OCR Text ---")
    print(raw_text)
    print("-------------------------------\n")
    
    if not raw_text:
        print("Failed to get text from OCR.")
        return

    # 2. LLM Extraction
    print("Running LLM Extraction...")
    items = await llm_service.extract_items_from_text(raw_text)
    print("\n--- Extracted Items ---")
    for item in items:
        print(item)

if __name__ == "__main__":
    asyncio.run(test_full_pipeline())
