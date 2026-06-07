import os


class Settings:
    project_id: str = os.getenv("GOOGLE_CLOUD_PROJECT", "safety-monitor-2026")
    environment: str = os.getenv("ENV", "development")
    secret_key: str = os.getenv("SECRET_KEY", "change-me-in-production")
    database: str = os.getenv("DATABASE", "firestore" if os.getenv("ENV") == "production" else "local")

    # Multi-tenant defaults
    default_regulator_email: str = os.getenv("REGULATOR_EMAIL", "admin@aviasafe.com")


settings = Settings()
