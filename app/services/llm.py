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
You are an expert medical bill data extractor. Your task is to extract medical items from the provided document text (which may be in Markdown format with tables).

Document Content:
{ocr_text}

Rules:
1. EXAMINE HTML TABLES CAREFULLY. The data is in HTML format with `<table>`, `<tr>`, `<td>` tags.
2. Identify the core medicine/procedure name even if the column header is not "Medicine Name" (could be "Description", "Items", "Service", etc.).
3. Extract the LINE ITEM PRICE (not the unit price). Look for columns like "Total", "Net Amount", "Amount", "Price", or any numeric value at the end of the row.
4. Extract ONLY medical items (medicines, tablets, syrups, injections, lab tests, procedures) with their prices.
5. Ignore: person names, addresses, tax lines, totals, "round off", "discount", "payable amount", headers.
6. For each item found in the table, extract:
   - "item_name": The full name of the medicine or test.
   - "quantity": The quantity as a number (default to 1 if not found).
   - "price": The total price for this line item (as a number).
7. Output strictly in JSON format. Do not return markdown code blocks or any other text.
8. If the price is missing, set "price": 0.0.

Output Format:
{{
  "medical_items": [
    {{
      "item_name": "Dolo 650",
      "quantity": 10,
      "price": 30.50
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
