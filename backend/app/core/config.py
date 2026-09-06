import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "WeatherGPT"
    API_V1_STR: str = "/api"
    
    # MongoDB Atlas Settings
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb+srv://demo:demo@cluster0.mongodb.net/weathergpt?retryWrites=true&w=majority")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "weathergpt")

    # JWT Settings
    JWT_SECRET: str = os.getenv("JWT_SECRET", "weathergpt_super_secret_jwt_key_2026_change_in_prod")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")) # 24 hours

    # AI / LLM Settings
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # Email Settings (SMTP)
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "noreply@weathergpt.com")

settings = Settings()
