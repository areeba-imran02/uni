import os
from dotenv import load_dotenv
load_dotenv()
class Settings:
    app_name = os.getenv("APP_NAME", "UniVerse AI")
    secret_key = os.getenv("SECRET_KEY", "dev-only-change-this-secret-key")
    database_url = os.getenv("DATABASE_URL", "sqlite:///./universe.db")
    cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    gemini_api_key = os.getenv("GEMINI_API_KEY", "")
    demo_mode = os.getenv("DEMO_MODE", "true").lower() == "true"
settings = Settings()
