import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- App ---
    APP_NAME: str = "ClientIQ"
    ENV: str = os.getenv("ENV", "development")

    # --- Auth / JWT ---
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "dev-secret-change-me-in-prod")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8  # 8h shift for consultants

    # --- LLM (Groq) ---
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    # --- Vector store ---
    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "./chroma_data")
    CHROMA_COLLECTION: str = "clientiq_reports"

    # --- Mock enterprise data sources (MCP connectors) ---
    POSTGRES_DSN: str = os.getenv("POSTGRES_DSN", "mock://sales-warehouse")
    SLACK_WORKSPACE: str = os.getenv("SLACK_WORKSPACE", "mock://acme-support")
    JIRA_PROJECT: str = os.getenv("JIRA_PROJECT", "mock://ops-board")
    SALESFORCE_ORG: str = os.getenv("SALESFORCE_ORG", "mock://crm")
    GOOGLE_SHEETS_ID: str = os.getenv("GOOGLE_SHEETS_ID", "mock://forecast-sheet")

    CORS_ORIGINS_RAW: str = os.getenv(
    "CORS_ORIGINS", "http://localhost:5173,http://localhost:3000"
)

    class Config:
        env_file = ".env"
        extra="ignore"

    @property
    def CORS_ORIGINS(self) -> list:
        return [origin.strip() for origin in self.CORS_ORIGINS_RAW.split(",") if origin.strip()]


settings = Settings()
