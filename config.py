import os

from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'cafe_fusion.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    STAFF_SETUP_CODE = os.getenv("STAFF_SETUP_CODE", "")
