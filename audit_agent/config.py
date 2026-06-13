"""
Configuration — chargée depuis les variables d'environnement.
SMD GLOBAL CONSULTING LLC
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Anthropic
    anthropic_api_key: str
    claude_model: str = "claude-sonnet-4-6"

    # PDF.co
    pdfco_api_key: str
    google_drive_template_url: str  # URL directe du template Word sur Drive

    # Email SMTP (Gmail App Password)
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str           # diallosouleymane19@gmail.com
    smtp_password: str       # App Password Gmail (16 caractères)
    email_from_name: str = "SMD GLOBAL CONSULTING LLC"

    # Notion
    notion_token: str
    notion_db_id: str        # ID de la base de données prospects Notion

    # Google Drive
    google_drive_folder_id: str   # Dossier "Audits RGPD" sur Drive
    google_service_account_json: str = ""  # JSON du compte de service (optionnel)

    # App
    app_secret_key: str = "change-me-in-production"
    debug: bool = False
    port: int = 8000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
