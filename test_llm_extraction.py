import asyncio
import sys
import os

# Add the project root to the path so we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.llm import llm_service

async def test_extraction():
    # Simulate Markdown output from Marker OCR
    md_table = """
# Medical Bill

| SL | DESCRIPTION | BATCH | EXP. | QTY | RATE | AMOUNT |
|---|---|---|---|---|---|---|
| 1 | PARACETAMOL 500MG | B123 | 12/25 | 10 | 1.50 | 15.00 |
| 2 | COUGH SYRUP | C456 | 11/24 | 2 | 45.00 | 90.00 |
| 3 | CONSULTATION | - | - | 1 | 500.00 | 500.00 |
| | | | | | | |
| | | | | **TOTAL** | | **605.00** |
"""
    
    print("Running LLM extraction on MD Table...")
    items = await llm_service.extract_items_from_text(md_table)
    print("\n--- Extracted Items ---")
    for item in items:
        print(item)

if __name__ == "__main__":
    asyncio.run(test_extraction())
