import os

class Config:
    SECRET_KEY = os.getenv("APP_SECRET_KEY")
    AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID")
    AUTH0_CLIENT_SECRET = os.getenv("AUTH0_CLIENT_SECRET")
    AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
    FRONTEND_URL = os.getenv("FRONTEND_URL")