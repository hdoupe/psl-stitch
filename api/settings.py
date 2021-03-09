from typing import Optional
from fastapi import FastAPI
from pydantic import BaseSettings


class Settings(BaseSettings):
    CS_BASE_URL: str = "https://compute.studio"
    SECRET_KEY: str
    CLIENT_ID: str
    CLIENT_SECRET: str

    API_URL: str
    REDIRECT_URI_PATH: Optional[str] = "/oauth2/access/"

    FRONTEND_URL: str

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
