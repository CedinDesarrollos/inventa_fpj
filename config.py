import os

class Settings:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///local.db")
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    PROJECT_SLUG = os.getenv("PROJECT_SLUG", "agromax")
    PROJECT_NAME = os.getenv("PROJECT_NAME", "Agromax")
    BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

    DEFAULT_ADMIN_EMAIL = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@example.com")
    DEFAULT_ADMIN_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin")
