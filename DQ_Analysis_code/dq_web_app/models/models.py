"""
Enterprise Data Quality Platform - Database Models
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import json

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """User model"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100))
    role = db.Column(db.String(20), nullable=False, default='analyst')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime)
    
    # Relationships
    dq_runs = db.relationship('DQRun', backref='user', lazy='dynamic')
    alerts_assigned = db.relationship('Alert', foreign_keys='Alert.assigned_to', backref='assignee', lazy='dynamic')
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password"""
        return check_password_hash(self.password_hash, password)
    
    def is_locked(self):
        """Check if account is locked"""
        if self.locked_until and self.locked_until > datetime.utcnow():
            return True
        return False
    
    def has_permission(self, permission):
        """Check if user has permission"""
        role_permissions = {
            'admin': ['all'],
            'manager': ['view_all', 'create_rules', 'manage_alerts', 'generate_reports'],
            'analyst': ['view_own', 'run_analysis', 'view_reports'],
            'viewer': ['view_own', 'view_reports']
        }
        user_perms = role_permissions.get(self.role, [])
        return 'all' in user_perms or permission in user_perms
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }


class Role(db.Model):
    """Role model"""
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    role_name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    permissions = db.Column(db.Text)  # JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_permissions(self):
        """Get permissions as list"""
        return json.loads(self.permissions) if self.permissions else []
    
    def set_permissions(self, perms):
        """Set permissions from list"""
        self.permissions = json.dumps(perms)


class DQRun(db.Model):
    """DQ Analysis Run model"""
    __tablename__ = 'dq_runs'
    
    id = db.Column(db.Integer, primary_key=True)
    run_id = db.Column(db.String(50), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    dataset_name = db.Column(db.String(200), nullable=False)
    file_path = db.Column(db.String(500))
    file_size = db.Column(db.Integer)
    file_type = db.Column(db.String(20))
    total_records = db.Column(db.Integer)
    total_columns = db.Column(db.Integer)
    dq_score = db.Column(db.Numeric(5, 2))
    status = db.Column(db.String(20), default='pending')
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    execution_time = db.Column(db.Numeric(10, 2))
    error_message = db.Column(db.Text)
    config_used = db.Column(db.Text)  # JSON string
    
    # Relationships
    metrics = db.relationship('DQMetric', backref='run', lazy='dynamic', cascade='all, delete-orphan')
    anomalies = db.relationship('DQAnomaly', backref='run', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'run_id': self.run_id,
            'dataset_name': self.dataset_name,
            'file_type': self.file_type,
            'total_records': self.total_records,
            'total_columns': self.total_columns,
            'dq_score': float(self.dq_score) if self.dq_score else None,
            'status': self.status,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'execution_time': float(self.execution_time) if self.execution_time else None
        }


class DQMetric(db.Model):
    """DQ Metric model"""
    __tablename__ = 'dq_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    run_id = db.Column(db.String(50), db.ForeignKey('dq_runs.run_id'), nullable=False)
    metric_name = db.Column(db.String(100), nullable=False)
    metric_value = db.Column(db.Numeric(10, 2))
    metric_category = db.Column(db.String(50))
    column_name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class DQAnomaly(db.Model):
    """DQ Anomaly model"""
    __tablename__ = 'dq_anomalies'
    
    id = db.Column(db.Integer, primary_key=True)
    run_id = db.Column(db.String(50), db.ForeignKey('dq_runs.run_id'), nullable=False)
    anomaly_type = db.Column(db.String(50), nullable=False)
    column_name = db.Column(db.String(100))
    row_number = db.Column(db.Integer)
    severity = db.Column(db.String(20))
    description = db.Column(db.Text)
    value_found = db.Column(db.Text)
    expected_value = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class BusinessRule(db.Model):
    """Business Rule model"""
    __tablename__ = 'business_rules'
    
    id = db.Column(db.Integer, primary_key=True)
    rule_id = db.Column(db.String(50), unique=True, nullable=False)
    rule_name = db.Column(db.String(200), nullable=False)
    rule_type = db.Column(db.String(50), nullable=False)
    rule_category = db.Column(db.String(50))
    column_name = db.Column(db.String(100))
    rule_definition = db.Column(db.Text, nullable=False)  # JSON string
    severity = db.Column(db.String(20), default='medium')
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    version = db.Column(db.Integer, default=1)
    
    def get_definition(self):
        """Get rule definition as dict"""
        return json.loads(self.rule_definition) if self.rule_definition else {}
    
    def set_definition(self, definition):
        """Set rule definition from dict"""
        self.rule_definition = json.dumps(definition)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'rule_id': self.rule_id,
            'rule_name': self.rule_name,
            'rule_type': self.rule_type,
            'rule_category': self.rule_category,
            'column_name': self.column_name,
            'rule_definition': self.get_definition(),
            'severity': self.severity,
            'is_active': self.is_active,
            'version': self.version,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Alert(db.Model):
    """Alert model"""
    __tablename__ = 'alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    alert_id = db.Column(db.String(50), unique=True, nullable=False)
    run_id = db.Column(db.String(50), db.ForeignKey('dq_runs.run_id'))
    alert_type = db.Column(db.String(50), nullable=False)
    severity = db.Column(db.String(20), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    is_resolved = db.Column(db.Boolean, default=False)
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)
    resolved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'alert_id': self.alert_id,
            'alert_type': self.alert_type,
            'severity': self.severity,
            'title': self.title,
            'message': self.message,
            'is_read': self.is_read,
            'is_resolved': self.is_resolved,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class MetadataCatalog(db.Model):
    """Metadata Catalog model"""
    __tablename__ = 'metadata_catalog'
    
    id = db.Column(db.Integer, primary_key=True)
    dataset_name = db.Column(db.String(200), nullable=False)
    column_name = db.Column(db.String(100), nullable=False)
    data_type = db.Column(db.String(50))
    semantic_type = db.Column(db.String(50))
    description = db.Column(db.Text)
    business_definition = db.Column(db.Text)
    sample_values = db.Column(db.Text)
    null_count = db.Column(db.Integer)
    unique_count = db.Column(db.Integer)
    min_value = db.Column(db.Text)
    max_value = db.Column(db.Text)
    avg_value = db.Column(db.Numeric(15, 2))
    std_dev = db.Column(db.Numeric(15, 2))
    pattern = db.Column(db.Text)
    last_profiled = db.Column(db.DateTime, default=datetime.utcnow)
    profiled_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    __table_args__ = (db.UniqueConstraint('dataset_name', 'column_name'),)


class HistoricalTrend(db.Model):
    """Historical Trend model"""
    __tablename__ = 'historical_trends'
    
    id = db.Column(db.Integer, primary_key=True)
    dataset_name = db.Column(db.String(200), nullable=False)
    metric_name = db.Column(db.String(100), nullable=False)
    metric_value = db.Column(db.Numeric(10, 2))
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)
    run_id = db.Column(db.String(50), db.ForeignKey('dq_runs.run_id'))


class ReconciliationRun(db.Model):
    """Reconciliation Run model"""
    __tablename__ = 'reconciliation_runs'
    
    id = db.Column(db.Integer, primary_key=True)
    recon_id = db.Column(db.String(50), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    source_name = db.Column(db.String(200), nullable=False)
    target_name = db.Column(db.String(200), nullable=False)
    recon_type = db.Column(db.String(50))
    source_count = db.Column(db.Integer)
    target_count = db.Column(db.Integer)
    match_count = db.Column(db.Integer)
    mismatch_count = db.Column(db.Integer)
    match_percentage = db.Column(db.Numeric(5, 2))
    status = db.Column(db.String(20), default='pending')
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Relationships
    details = db.relationship('ReconciliationDetail', backref='recon_run', lazy='dynamic', cascade='all, delete-orphan')


class ReconciliationDetail(db.Model):
    """Reconciliation Detail model"""
    __tablename__ = 'reconciliation_details'
    
    id = db.Column(db.Integer, primary_key=True)
    recon_id = db.Column(db.String(50), db.ForeignKey('reconciliation_runs.recon_id'), nullable=False)
    check_type = db.Column(db.String(50), nullable=False)
    check_name = db.Column(db.String(100))
    source_value = db.Column(db.Text)
    target_value = db.Column(db.Text)
    match_status = db.Column(db.String(20))
    difference = db.Column(db.Text)


class AuditLog(db.Model):
    """Audit Log model"""
    __tablename__ = 'audit_log'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(100), nullable=False)
    entity_type = db.Column(db.String(50))
    entity_id = db.Column(db.String(50))
    old_value = db.Column(db.Text)
    new_value = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Session(db.Model):
    """Session model"""
    __tablename__ = 'sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)


class Report(db.Model):
    """Report model"""
    __tablename__ = 'reports'
    
    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.String(50), unique=True, nullable=False)
    run_id = db.Column(db.String(50), db.ForeignKey('dq_runs.run_id'))
    report_type = db.Column(db.String(50), nullable=False)
    report_name = db.Column(db.String(200), nullable=False)
    file_path = db.Column(db.String(500))
    file_size = db.Column(db.Integer)
    generated_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)


class SystemSetting(db.Model):
    """System Setting model"""
    __tablename__ = 'system_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(100), unique=True, nullable=False)
    setting_value = db.Column(db.Text)
    setting_type = db.Column(db.String(20))
    description = db.Column(db.Text)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_value(self):
        """Get typed value"""
        if self.setting_type == 'integer':
            return int(self.setting_value)
        elif self.setting_type == 'boolean':
            return self.setting_value.lower() in ['true', '1', 'yes']
        elif self.setting_type == 'json':
            return json.loads(self.setting_value)
        return self.setting_value

# Made with Bob
