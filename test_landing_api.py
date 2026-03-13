import os
from dotenv import load_dotenv
import requests

load_dotenv()

def test_landing_api():
    api_key = os.getenv("LANDING_API_KEY")
    if not api_key:
        print("Error: LANDING_API_KEY not found in .env")
        return

    endpoint = "https://api.va.landing.ai/v1/ade/parse"
    
    # Use an existing file for testing
    file_path = "test_bill.png"
    if not os.path.exists(file_path):
        # Try another one if test_bill.png doesn't exist
        for f in os.listdir("."):
            if f.endswith((".png", ".jpg", ".jpeg", ".pdf")):
                file_path = f
                break
    
    print(f"Testing Landing AI API with file: {file_path}")
    print(f"API Key: {api_key[:5]}...{api_key[-5:]}")

    try:
        mime_type = 'application/pdf' if file_path.lower().endswith('.pdf') else 'image/png'
        if file_path.lower().endswith(('.jpg', '.jpeg')):
            mime_type = 'image/jpeg'
            
        with open(file_path, "rb") as f:
            files = {
                'document': (os.path.basename(file_path), f, mime_type)
            }
            headers = {
                "Authorization": f"Bearer {api_key}"
            }
            
            response = requests.post(
                endpoint,
                files=files,
                headers=headers,
                timeout=60
            )
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("API Key is working fine!")
            data = response.json()
            # print(f"Response data: {data}")
            if 'chunks' in data:
                print(f"Extracted {len(data['chunks'])} chunks.")
                for i, chunk in enumerate(data['chunks']):
                    if 'markdown' in chunk:
                        print(f"Chunk {i} text length: {len(chunk['markdown'])}")
                        # print(f"Sample: {chunk['markdown'][:100]}...")
            elif 'data' in data and 'markdown' in data['data']:
                print(f"Extracted markdown length: {len(data['data']['markdown'])}")
            else:
                print("Response format unknown but status is 200.")
        else:
            print(f"API Error: {response.text}")

    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_landing_api()
