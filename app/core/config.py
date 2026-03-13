from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Medical Bill Validator"
    DATABASE_URL: str = "sqlite:///./medical_bills.db"
    REDIS_URL: str = "redis://localhost:6379"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    MISTRAL_MODEL: str = "mistral"
    LANDING_API_KEY: str = ""  # LandingAI API key for OCR (set in .env)

    class Config:
        env_file = ".env"

settings = Settings()
