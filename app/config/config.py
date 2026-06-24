import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "WhatsApp Routing Engine"
    DEBUG: bool = True
    
    # Meta WhatsApp API Credentials
    VERIFY_TOKEN: str
    META_ACCESS_TOKEN: str
    PHONE_NUMBER_ID: str
    META_API_VERSION: str = "v23.0"
    
    # Database Configuration
    MONGO_URI: str
    MONGO_DB_NAME: str

    # Read from .env file directly
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

# Instantiate for use across the application
settings = Settings()