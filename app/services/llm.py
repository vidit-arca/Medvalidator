import httpx
import json
from typing import List, Dict, Optional
from app.core.config import settings
from pydantic import BaseModel

class MappingResult(BaseModel):
    procedure_code: Optional[str]
    confidence: float
    reason: str

class LLMService:
    def __init__(self):
        self.base_url = f"{settings.OLLAMA_BASE_URL}/api/generate"
        self.model = settings.MISTRAL_MODEL

    async def map_procedure(self, ocr_text: str, candidates: List[Dict[str, str]]) -> MappingResult:
        prompt = self._construct_prompt(ocr_text, candidates)
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.base_url,
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json" 
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                result = response.json()
                response_text = result.get("response", "{}")
                
                # Parse JSON output
                data = json.loads(response_text)
                return MappingResult(
                    procedure_code=data.get("procedure_code"),
                    confidence=data.get("confidence", 0.0),
                    reason=data.get("reason", "No reason provided")
                )
            except Exception as e:
                print(f"LLM Error: {e}")
                return MappingResult(procedure_code=None, confidence=0.0, reason=f"LLM Error: {str(e)}")

    async def extract_items_from_text(self, ocr_text: str) -> List[Dict]:
        prompt = self._construct_extraction_prompt(ocr_text)
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.base_url,
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json"
                    },
                    timeout=120.0 # Increased timeout for extraction (Ollama can be slow)
                )
                response.raise_for_status()
                result = response.json()
                response_text = result.get("response", "{}")
                
                # Parse JSON output
                data = json.loads(response_text)
                items = data.get("medical_items", [])
                return items
            except json.JSONDecodeError as e:
                print(f"LLM Extraction Error - Invalid JSON: {e}")
                print(f"Raw response: {response_text[:200]}")
                return []
            except Exception as e:
                print(f"LLM Extraction Error: {e}")
                import traceback
                traceback.print_exc()
                return []

    def _construct_extraction_prompt(self, ocr_text: str) -> str:
        return f"""
You are an expert medical bill data extractor.
Your task is to extract individual medical items and their prices from the provided OCR text.

Document Content:
{ocr_text}

CRITICAL RULES:
1. The data is formatted as a Markdown table (rows separated by newlines, columns separated by `|`).
2. PROCESS THE TABLE ROW BY ROW. DO NOT combine or concatenate items from different rows together.
3. For EVERY SINGLE ROW in the table that contains a product, extract exactly ONE item.
4. The "item_name" is typically in the second or third column (e.g., "PRODUCT NAME", "Description").
5. The "price" or "AMOUNT" is typically in the last few columns. Extract the final line amount.
6. Extract ONLY medical items (medicines, tablets, lab tests). Ignore taxes, subtotals, and blank rows.
7. Output strictly in JSON format matching the schema below. Do not add any extra text.

Output Format:
{{
  "medical_items": [
    {{
      "item_name": "DYTOR 10 TAB",
      "quantity": 2,
      "price": 219.14
    }},
    {{
      "item_name": "DAPANARY-10M FORTE TAB",
      "quantity": 2,
      "price": 432.00
    }}
  ]
}}

Response:
"""

    def _construct_prompt(self, ocr_text: str, candidates: List[Dict[str, str]]) -> str:
        candidates_str = json.dumps(candidates, indent=2)
        return f"""
You are a medical coding expert. Your task is to map a messy OCR procedure description to a standard procedure code from a provided list.

Input OCR Text: "{ocr_text}"

Candidate Procedures:
{candidates_str}

Rules:
1. Select the best matching candidate based on semantic meaning.
2. If no candidate matches with high confidence, set "procedure_code" to null.
3. Output strictly in JSON format.
4. Do NOT validate prices. Only map the procedure.

Output Format:
{{
  "procedure_code": "CODE_FROM_CANDIDATES",
  "confidence": 0.95,
  "reason": "Explanation for the match"
}}

Response:
"""

llm_service = LLMService()
