"""
Enterprise Data Quality Platform - Main Application
"""
import os
import sys
from flask import Flask, render_template, redirect, url_for, flash
from flask_login import LoginManager, current_user, login_required
from flask_cors import CORS
import logging
from logging.handlers import RotatingFileHandler

# Add parent directory to path to import dq_engine
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import get_config
from models.models import db, User
from api import auth_bp, analysis_bp, rules_bp, alerts_bp, reports_bp, metadata_bp, trends_bp, recon_bp, admin_bp


def create_app(config_name=None):
    """Application factory"""
    app = Flask(__name__)
    
    # Load configuration
    config = get_config(config_name)
    app.config.from_object(config)
    
    # Ensure required directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['REPORTS_FOLDER'], exist_ok=True)
    os.makedirs(os.path.dirname(app.config['LOG_FILE']), exist_ok=True)
    
    # Initialize extensions
    db.init_app(app)
    CORS(app, origins=app.config['CORS_ORIGINS'])
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(analysis_bp, url_prefix='/api/analysis')
    app.register_blueprint(rules_bp, url_prefix='/api/rules')
    app.register_blueprint(alerts_bp, url_prefix='/api/alerts')
    app.register_blueprint(reports_bp, url_prefix='/api/reports')
    app.register_blueprint(metadata_bp, url_prefix='/api/metadata')
    app.register_blueprint(trends_bp, url_prefix='/api/trends')
    app.register_blueprint(recon_bp, url_prefix='/api/reconciliation')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    
    # Main routes
    @app.route('/')
    def index():
        """Home page - redirect to dashboard or login"""
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return redirect(url_for('auth.login'))
    
    @app.route('/dashboard')
    @login_required
    def dashboard():
        """Main dashboard"""
        return render_template('dashboard.html', title='Dashboard')
    
    @app.route('/upload')
    @login_required
    def upload():
        """Upload & Analyze page"""
        return render_template('upload.html', title='Upload & Analyze')
    
    @app.route('/results/<run_id>')
    @login_required
    def results(run_id):
        """Results page"""
        return render_template('results.html', title='Analysis Results', run_id=run_id)
    
    @app.route('/rules')
    @login_required
    def rules():
        """Rule Management page"""
        return render_template('rules.html', title='Rule Management')
    
    @app.route('/alerts')
    @login_required
    def alerts():
        """Alert Center page"""
        return render_template('alerts.html', title='Alert Center')
    
    @app.route('/metadata')
    @login_required
    def metadata():
        """Metadata Catalog page"""
        return render_template('metadata.html', title='Metadata Catalog')
    
    @app.route('/reports')
    @login_required
    def reports_page():
        """Reports page"""
        return render_template('reports.html', title='Reports')
    
    @app.route('/reconciliation')
    @login_required
    def reconciliation():
        """Reconciliation page"""
        return render_template('reconciliation.html', title='Reconciliation')
    
    @app.route('/trends')
    @login_required
    def trends():
        """Historical Trends page"""
        return render_template('trends.html', title='Historical Trends')
    
    @app.route('/admin')
    @login_required
    def admin():
        """Administration page"""
        if not current_user.has_permission('all'):
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('dashboard'))
        return render_template('admin.html', title='Administration')
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403
    
    # Context processors
    @app.context_processor
    def inject_config():
        """Inject config into templates"""
        return {
            'app_name': app.config['APP_NAME'],
            'version': app.config['VERSION']
        }
    
    # Setup logging
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler(
            app.config['LOG_FILE'],
            maxBytes=app.config['LOG_MAX_BYTES'],
            backupCount=app.config['LOG_BACKUP_COUNT']
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('DQ Platform startup')
    
    return app


def init_db(app):
    """Initialize database"""
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Check if admin user exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@dqplatform.com',
                full_name='System Administrator',
                role='admin',
                is_active=True
            )
            admin.set_password('admin123')  # Change in production!
            db.session.add(admin)
            db.session.commit()
            print('Admin user created: username=admin, password=admin123')


if __name__ == '__main__':
    app = create_app()
    
    # Initialize database
    init_db(app)
    
    # Run application
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )

# Made with Bob