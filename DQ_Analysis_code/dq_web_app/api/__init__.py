"""
Enterprise Data Quality Platform - API Package
"""
from .auth import auth_bp
from .analysis import analysis_bp
from .rules import rules_bp
from .alerts import alerts_bp
from .reports import reports_bp
from .metadata import metadata_bp
from .trends import trends_bp
from .reconciliation import recon_bp
from .admin import admin_bp

__all__ = [
    'auth_bp',
    'analysis_bp',
    'rules_bp',
    'alerts_bp',
    'reports_bp',
    'metadata_bp',
    'trends_bp',
    'recon_bp',
    'admin_bp'
]

# Made with Bob
