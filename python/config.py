import os

class Config:
    DEBUG = os.environ.get('DEBUG', 'False').lower() in ('true', '1', 't')
    ENV = os.environ.get('FLASK_ENV', 'production')

    # Feature Toggles
    ENABLE_PROMETHEUS = os.environ.get('ENABLE_PROMETHEUS', 'True').lower() in ('true', '1', 't')
    ENABLE_OPENTELEMETRY = os.environ.get('ENABLE_OPENTELEMETRY', 'True').lower() in ('true', '1', 't')

    # Weitere Konfigurationsoptionen hier
    # Weitere Konfigurationsoptionen hier
