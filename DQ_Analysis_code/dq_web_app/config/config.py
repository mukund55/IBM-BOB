"""
Enterprise Data Quality Platform - Configuration
"""
import os
from datetime import timedelta

class Config:
    """Base configuration"""
    
    # Application
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    APP_NAME = 'Enterprise Data Quality Platform'
    VERSION = '1.0.0'
    
    # Flask
    DEBUG = False
    TESTING = False
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///../database/dq_platform.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    
    # Session
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # File Upload
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
    ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls', 'txt', 'dat', 'json', 'xml'}
    
    # Reports
    REPORTS_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'reports')
    
    # DQ Engine
    DQ_ENGINE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'dq_engine')
    DQ_OUTPUT_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'dq_output')
    
    # Security
    BCRYPT_LOG_ROUNDS = 12
    MAX_LOGIN_ATTEMPTS = 5
    ACCOUNT_LOCKOUT_DURATION = timedelta(minutes=30)
    PASSWORD_MIN_LENGTH = 8
    
    # Pagination
    ITEMS_PER_PAGE = 25
    MAX_ITEMS_PER_PAGE = 100
    
    # Alerts
    ALERT_RETENTION_DAYS = 90
    DQ_SCORE_THRESHOLD_CRITICAL = 70
    DQ_SCORE_THRESHOLD_WARNING = 85
    
    # Performance
    MAX_CONCURRENT_ANALYSES = 5
    ANALYSIS_TIMEOUT_SECONDS = 300
    
    # Logging
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'logs/dq_platform.log'
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5
    
    # CORS
    CORS_ORIGINS = ['http://localhost:5000', 'http://127.0.0.1:5000']
    
    # API
    API_RATE_LIMIT = '100 per hour'
    API_VERSION = 'v1'
    
    # Email (optional)
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'noreply@dqplatform.com'
    
    # Celery (optional for async tasks)
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL') or 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND') or 'redis://localhost:6379/0'
    
    # Monitoring
    ENABLE_METRICS = True
    METRICS_PORT = 9090


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_ECHO = True
    SESSION_COOKIE_SECURE = False
    LOG_LEVEL = 'DEBUG'


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    
    # Override with environment variables in production
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    
    # Enhanced security for production
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'
    
    # Stricter rate limiting
    API_RATE_LIMIT = '50 per hour'


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(config_name=None):
    """Get configuration based on environment"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    return config.get(config_name, DevelopmentConfig)

# Made with Bob
