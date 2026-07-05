import os
import numpy as np
import tritonclient.http as httpclient
from app.core.config import settings

class MarkerOCRService:
    def __init__(self):
        # tritonclient expects host:port, without scheme
        url = settings.TRITON_SERVER_URL.replace("http://", "").replace("https://", "").rstrip('/')
        self.client = httpclient.InferenceServerClient(
            url=url,
            network_timeout=300.0,
            connection_timeout=300.0
        )
        self.model_name = settings.TRITON_MARKER_MODEL_NAME

    def extract_text(self, file_path: str) -> str:
        """
        Extracts text using Marker OCR deployed on Triton Inference Server.
        """
        if not os.path.exists(file_path):
            return ""

        try:
            with open(file_path, "rb") as f:
                file_bytes = f.read()

            input_data = np.array([file_bytes], dtype=np.object_)

            inputs = []
            inputs.append(httpclient.InferInput('PDF_BYTES', [1], "BYTES"))
            inputs[0].set_data_from_numpy(input_data)

            outputs = []
            outputs.append(httpclient.InferRequestedOutput('MARKDOWN'))

            response = self.client.infer(
                model_name=self.model_name,
                inputs=inputs,
                outputs=outputs,
                timeout=300
            )

            result_bytes = response.as_numpy('MARKDOWN')
            if result_bytes is not None and len(result_bytes) > 0:
                return result_bytes[0].decode('utf-8')
                
            return ""

        except Exception as e:
            print(f"Marker OCR Extraction Failed: {e}")
            return ""

marker_ocr_service = MarkerOCRService()
