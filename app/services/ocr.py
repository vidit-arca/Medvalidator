from unstructured.partition.auto import partition
from app.schemas import LineItemResponse
from typing import List
from decimal import Decimal
import re
import nltk
import pandas as pd
from io import StringIO
from unstructured.documents.elements import Table

class OCRService:
    def extract_text(self, file_path: str) -> str:
        try:
            nltk.download('punkt', quiet=True)
            nltk.download('averaged_perceptron_tagger', quiet=True)
        except:
            pass

        # Use hi_res strategy for PDFs to better capture tables
        if file_path.lower().endswith('.pdf'):
            from unstructured.partition.pdf import partition_pdf
            elements = partition_pdf(
                filename=file_path,
                strategy="hi_res",
                extract_images_in_pdf=False, 
                infer_table_structure=True
            )
        else:
            # Fallback for images
            elements = partition(filename=file_path)
            
        text_parts = []
        for element in elements:
            if isinstance(element, Table) and element.metadata.text_as_html:
                try:
                    # Parse HTML table to DataFrame
                    dfs = pd.read_html(StringIO(element.metadata.text_as_html))
                    if dfs:
                        df = dfs[0]
                        # Convert each row to a string representation
                        # We join columns with space to mimic a line of text
                        for _, row in df.iterrows():
                            # Filter out None/NaN
                            row_text = " ".join([str(val) for val in row.values if pd.notna(val)])
                            text_parts.append(row_text)
                except Exception as e:
                    # Fallback to string representation if HTML parsing fails
                    text_parts.append(str(element))
            else:
                text_parts.append(str(element))

        text = "\n".join(text_parts)
        
        # Fallback: If text looks garbage (e.g. "Charge Charge" loop) or is empty, try Direct OCR
        if not text.strip() or "Charge Charge" in text:
            print("Unstructured extraction failed or produced garbage. Switching to Direct OCR.")
            return self._extract_with_tesseract(file_path)
            
        return text

    def _extract_with_tesseract(self, file_path: str) -> str:
        try:
            from pdf2image import convert_from_path
            import pytesseract
            
            images = convert_from_path(file_path)
            text_parts = []
            for image in images:
                text_parts.append(pytesseract.image_to_string(image))
            return "\n".join(text_parts)
        except Exception as e:
            print(f"Direct OCR failed: {e}")
            return ""

    def parse_line_items(self, text: str) -> List[LineItemResponse]:
        # This is a heuristic parser. In a real world, this would be much more complex
        # or use a specialized model.
        # We look for lines that end with a number (price).
        
        lines = text.split('\n')
        items = []
        
        # Regex for a line item: Description ... Price
        # Example: "Chest X-Ray 50.00" or "Consultation 500"
        # We assume the last number is the price.
        price_pattern = re.compile(r'(.+?)\s+([\d,]+\.?\d{0,2})$')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            match = price_pattern.search(line)
            if match:
                description = match.group(1).strip()
                price_str = match.group(2).replace(',', '')
                
                try:
                    price = Decimal(price_str)
                    # Filter out likely noise (e.g. page numbers, dates)
                    if price <= 0:
                        continue
                        
                    # Basic heuristic: Description shouldn't be too short or look like a date
                    if len(description) < 3:
                        continue
                        
                    # Filter out "Total" lines and other noise
                    noise_keywords = ["total", "round off", "payable amount", "discount amount", "gross amount", "shipping"]
                    if any(keyword in description.lower() for keyword in noise_keywords):
                        continue
                        
                    items.append(LineItemResponse(
                        raw_ocr_text=description,
                        extracted_price=price,
                        quantity=1, # Default to 1 for now
                        mapped_procedure_code=None,
                        mapping_confidence=0.0,
                        variance_percent=None,
                        line_decision=None
                    ))
                except ValueError:
                    continue
                    
        return items

ocr_service = OCRService()
