import os
import sys
from app.services.marker_ocr import marker_ocr_service
from app.core.config import settings

def test_marker_ocr():
    print(f"Testing Triton Server URL: {settings.TRITON_SERVER_URL}")
    print(f"Testing Model Name: {settings.TRITON_MARKER_MODEL_NAME}")
    
    if len(sys.argv) < 2:
        print("Usage: python test_marker_api.py <path_to_bill_image_or_pdf>")
        return
        
    file_path = sys.argv[1]
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
        
    print(f"\nSending {file_path} to Marker OCR on Triton...")
    text = marker_ocr_service.extract_text(file_path)
    
    print("\n" + "="*50)
    print("EXTRACTION RESULT:")
    print("="*50)
    print(text)
    print("="*50)

if __name__ == "__main__":
    test_marker_ocr()
