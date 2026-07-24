import os
import numpy as np
import tritonclient.http as httpclient

class MarkerOCRService:
    def __init__(self):
        # Connect to your Triton server (Triton HTTP defaults to port 8000)
        self.client = httpclient.InferenceServerClient(
            url="192.168.112.2:8000", 
            network_timeout=600.0, 
            connection_timeout=600.0
        )
        self.model_name = "marker_model"

    def extract_text(self, file_path: str) -> str:
        """
        Extracts text using Marker OCR deployed on Triton Inference Server.
        """
        if not os.path.exists(file_path):
            return ""

        try:
            # Read your PDF (or image)
            with open(file_path, "rb") as f:
                pdf_bytes = f.read()

            # Setup the input tensor to match your config.pbtxt
            input_tensor = httpclient.InferInput("PDF_BYTES", [1], "BYTES")
            input_tensor.set_data_from_numpy(np.array([pdf_bytes], dtype=object))

            # Setup the output tensor
            output_tensor = httpclient.InferRequestedOutput("MARKDOWN")

            # Run Inference
            print(f"Sending {file_path} to Triton at 192.168.112.2:8000...")
            response = self.client.infer(
                model_name=self.model_name, 
                inputs=[input_tensor], 
                outputs=[output_tensor]
            )

            # Decode the result
            markdown = response.as_numpy("MARKDOWN")[0].decode("utf-8")
            return markdown

        except Exception as e:
            print(f"Marker OCR Extraction Failed: {e}")
            return ""

marker_ocr_service = MarkerOCRService()
