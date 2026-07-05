from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Medical Bill Validator"
    DATABASE_URL: str = "sqlite:///./medical_bills.db"
    REDIS_URL: str = "redis://localhost:6379"
    OLLAMA_BASE_URL: str = "http://192.168.112.2:11434"
    MISTRAL_MODEL: str = "mistral"
    TRITON_SERVER_URL: str = "http://192.168.112.2:8000"  # Triton inference server URL
    TRITON_MARKER_MODEL_NAME: str = "marker_model"  # Name of the Marker model on Triton

    class Config:
        env_file = ".env"

settings = Settings()
