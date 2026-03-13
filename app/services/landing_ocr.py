import os
import requests
from app.core.config import settings

class LandingOCRService:
    def __init__(self):
        self.api_key = settings.LANDING_API_KEY
        if not self.api_key:
            raise ValueError("LANDING_API_KEY is not configured in settings. Please add it to your .env file.")
        # Endpoint found via library inspection: /v1/ade/parse
        # Base URL: https://api.va.landing.ai
        self.endpoint = "https://api.va.landing.ai/v1/ade/parse"

    def extract_text(self, file_path: str) -> str:
        """
        Extracts text using Landing AI's Agentic Document Extraction API via direct HTTP call.
        """
        if not os.path.exists(file_path):
            return ""

        try:
            # Prepare file for upload
            # The API matches file extension to mime type usually, or we can explictly set it
            mime_type = 'application/pdf' if file_path.lower().endswith('.pdf') else 'image/png'
            if file_path.lower().endswith('.jpg') or file_path.lower().endswith('.jpeg'):
                mime_type = 'image/jpeg'
                
            with open(file_path, "rb") as f:
                files = {
                    'document': (os.path.basename(file_path), f, mime_type)
                }
                
                # Auth: Bearer Token
                headers = {
                    "Authorization": f"Bearer {self.api_key}"
                }
                
                response = requests.post(
                    self.endpoint,
                    files=files,
                    headers=headers,
                    timeout=60
                )
            
            if response.status_code == 200:
                data = response.json()
                # Structure based on library analysis: returns ParseResponse which has 'chunks'
                # Let's inspect the JSON structure if we need to debug, but assume it matches
                # { "data": { "markdown": ... } } OR { "chunks": [ { "markdown": ... } ] }
                
                # Based on library logic:
                # result = self.post(..., cast_to=ParseResponse)
                # ParseResponse usually reflects the JSON.
                
                # Check for 'chunks'
                text_parts = []
                if 'chunks' in data:
                    for chunk in data['chunks']:
                        if 'markdown' in chunk:
                            text_parts.append(chunk['markdown'])
                    
                    full_text = "\n\n".join(text_parts)
                    return full_text
                
                # Check for 'data' -> 'markdown' (older API style or alternative)
                if 'data' in data and 'markdown' in data['data']:
                     return data['data']['markdown']
                     
                return str(data)

            else:
                print(f"Landing AI API Error: {response.status_code} - {response.text}")
                return ""

        except Exception as e:
            print(f"Landing AI Extraction Failed: {e}")
            return ""

landing_ocr_service = LandingOCRService()
