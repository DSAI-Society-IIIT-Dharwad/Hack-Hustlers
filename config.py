import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'telemedicine-secure-key-2026-xK9mP2')
    JWT_SECRET = os.getenv('JWT_SECRET', 'jwt-secret-healthcare-aI7nQ3')
    JWT_EXPIRATION_HOURS = 24
    DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'telemedicine.db')
    CORS_ORIGINS = ['*']
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
