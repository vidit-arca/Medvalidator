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

    async def extract_items_from_text(self, parsed_json_str: str) -> List[Dict]:
        prompt = self._construct_extraction_prompt(parsed_json_str)
        
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

    def _construct_extraction_prompt(self, parsed_json_str: str) -> str:
        return f"""
You are an expert medical document data extractor.
You are receiving the extracted content from a medical bill or prescription. 
It may be a JSON array of table rows, or raw OCR text.

Document Content:
{parsed_json_str}

CRITICAL EXTRACTION RULES:

1. **First, identify the document type based on the JSON keys**.

2. **If it is a GST Invoice / Medicine Bill (Has keys like AMOUNT, NETAMT, MRP)**:
   - Extract each medicine item with its name, quantity, and the FINAL amount.
   - DO NOT extract MRP or RATE as the price. Look for keys like `AMOUNT`, `NETAMT`, `Gross Amount`.
   - Ignore dictionaries representing taxes, GST, subtotals, and grand total.

3. **If it is a Prescription Slip / NASLIP (Has keys like IQT, PQT, Nomenclature, but NO amounts)**:
   - Extract each medicine with its name and quantity from the `IQT` or `Qty` key.
   - Set price to 0.0 for all items since no prices are available on the document.
   - Ignore items where the quantity is "N/A" (not dispensed).

4. Extract ONLY medical items (medicines, tablets, lab tests). 
5. Output strictly in JSON format matching the schema below. Do not add any extra text.
6. NEVER hallucinate names. Extract the actual medicine names from the JSON content!

EXAMPLE - GST Invoice output:
{{"medical_items": [
  {{"item_name": "BUDECORT 0.5 RESP", "quantity": 60, "price": 1599.00}},
  {{"item_name": "DUOLIN RESPULES 3", "quantity": 60, "price": 1496.40}}
]}}

EXAMPLE - Prescription output:
{{"medical_items": [
  {{"item_name": "ATORVASTATIN 20 MG TAB", "quantity": 15, "price": 0.0}},
  {{"item_name": "PANTOPRAZOLE 40 MG TAB", "quantity": 30, "price": 0.0}}
]}}

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
