import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-prod')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///jobs.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # API Keys (optional)
    # France Travail (ex-Pôle Emploi) - https://francetravail.io
    FRANCETRAVAIL_CLIENT_ID = os.environ.get('FRANCETRAVAIL_CLIENT_ID')
    FRANCETRAVAIL_CLIENT_SECRET = os.environ.get('FRANCETRAVAIL_CLIENT_SECRET')

    # Careerjet - https://www.careerjet.com/partners/api/
    CAREERJET_AFFID = os.environ.get('CAREERJET_AFFID')

    # Adzuna - https://developer.adzuna.com/
    ADZUNA_APP_ID = os.environ.get('ADZUNA_APP_ID')
    ADZUNA_API_KEY = os.environ.get('ADZUNA_API_KEY')

    # Fetcher settings
    FETCH_TIMEOUT = int(os.environ.get('FETCH_TIMEOUT', 30))
    MAX_JOBS_PER_SOURCE = int(os.environ.get('MAX_JOBS_PER_SOURCE', 100))


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
