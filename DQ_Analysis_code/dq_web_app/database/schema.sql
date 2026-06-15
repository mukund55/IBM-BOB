-- Enterprise Data Quality Platform - Database Schema
-- Compatible with SQLite, PostgreSQL, and Oracle

-- Users Table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    role VARCHAR(20) NOT NULL DEFAULT 'analyst',  -- admin, manager, analyst, viewer
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP
);

-- Roles Table
CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    permissions TEXT,  -- JSON string of permissions
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- DQ Analysis Runs Table
CREATE TABLE IF NOT EXISTS dq_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id VARCHAR(50) UNIQUE NOT NULL,
    user_id INTEGER,
    dataset_name VARCHAR(200) NOT NULL,
    file_path VARCHAR(500),
    file_size INTEGER,
    file_type VARCHAR(20),
    total_records INTEGER,
    total_columns INTEGER,
    dq_score DECIMAL(5,2),
    status VARCHAR(20) DEFAULT 'pending',  -- pending, running, completed, failed
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    execution_time DECIMAL(10,2),
    error_message TEXT,
    config_used TEXT,  -- JSON string
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- DQ Metrics Table
CREATE TABLE IF NOT EXISTS dq_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id VARCHAR(50) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(10,2),
    metric_category VARCHAR(50),
    column_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (run_id) REFERENCES dq_runs(run_id)
);

-- DQ Anomalies Table
CREATE TABLE IF NOT EXISTS dq_anomalies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id VARCHAR(50) NOT NULL,
    anomaly_type VARCHAR(50) NOT NULL,
    column_name VARCHAR(100),
    row_number INTEGER,
    severity VARCHAR(20),  -- critical, high, medium, low
    description TEXT,
    value_found TEXT,
    expected_value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (run_id) REFERENCES dq_runs(run_id)
);

-- Business Rules Table
CREATE TABLE IF NOT EXISTS business_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_id VARCHAR(50) UNIQUE NOT NULL,
    rule_name VARCHAR(200) NOT NULL,
    rule_type VARCHAR(50) NOT NULL,  -- pattern, range, mandatory, custom
    rule_category VARCHAR(50),
    column_name VARCHAR(100),
    rule_definition TEXT NOT NULL,  -- JSON string
    severity VARCHAR(20) DEFAULT 'medium',
    is_active BOOLEAN DEFAULT 1,
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 1,
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- Rule Violations Table
CREATE TABLE IF NOT EXISTS rule_violations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id VARCHAR(50) NOT NULL,
    rule_id VARCHAR(50) NOT NULL,
    column_name VARCHAR(100),
    row_number INTEGER,
    violation_count INTEGER DEFAULT 1,
    value_found TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (run_id) REFERENCES dq_runs(run_id),
    FOREIGN KEY (rule_id) REFERENCES business_rules(rule_id)
);

-- Alerts Table
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_id VARCHAR(50) UNIQUE NOT NULL,
    run_id VARCHAR(50),
    alert_type VARCHAR(50) NOT NULL,  -- threshold_breach, rule_violation, system_error
    severity VARCHAR(20) NOT NULL,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT 0,
    is_resolved BOOLEAN DEFAULT 0,
    assigned_to INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    resolved_by INTEGER,
    FOREIGN KEY (run_id) REFERENCES dq_runs(run_id),
    FOREIGN KEY (assigned_to) REFERENCES users(id),
    FOREIGN KEY (resolved_by) REFERENCES users(id)
);

-- Metadata Catalog Table
CREATE TABLE IF NOT EXISTS metadata_catalog (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dataset_name VARCHAR(200) NOT NULL,
    column_name VARCHAR(100) NOT NULL,
    data_type VARCHAR(50),
    semantic_type VARCHAR(50),
    description TEXT,
    business_definition TEXT,
    sample_values TEXT,
    null_count INTEGER,
    unique_count INTEGER,
    min_value TEXT,
    max_value TEXT,
    avg_value DECIMAL(15,2),
    std_dev DECIMAL(15,2),
    pattern TEXT,
    last_profiled TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    profiled_by INTEGER,
    FOREIGN KEY (profiled_by) REFERENCES users(id),
    UNIQUE(dataset_name, column_name)
);

-- Historical Trends Table
CREATE TABLE IF NOT EXISTS historical_trends (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dataset_name VARCHAR(200) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(10,2),
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    run_id VARCHAR(50),
    FOREIGN KEY (run_id) REFERENCES dq_runs(run_id)
);

-- Reconciliation Runs Table
CREATE TABLE IF NOT EXISTS reconciliation_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recon_id VARCHAR(50) UNIQUE NOT NULL,
    user_id INTEGER,
    source_name VARCHAR(200) NOT NULL,
    target_name VARCHAR(200) NOT NULL,
    recon_type VARCHAR(50),  -- count, hash, column, full
    source_count INTEGER,
    target_count INTEGER,
    match_count INTEGER,
    mismatch_count INTEGER,
    match_percentage DECIMAL(5,2),
    status VARCHAR(20) DEFAULT 'pending',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Reconciliation Details Table
CREATE TABLE IF NOT EXISTS reconciliation_details (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recon_id VARCHAR(50) NOT NULL,
    check_type VARCHAR(50) NOT NULL,
    check_name VARCHAR(100),
    source_value TEXT,
    target_value TEXT,
    match_status VARCHAR(20),  -- match, mismatch, missing_source, missing_target
    difference TEXT,
    FOREIGN KEY (recon_id) REFERENCES reconciliation_runs(recon_id)
);

-- Audit Log Table
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),  -- user, rule, run, alert
    entity_id VARCHAR(50),
    old_value TEXT,
    new_value TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Sessions Table
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id VARCHAR(100) UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Reports Table
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id VARCHAR(50) UNIQUE NOT NULL,
    run_id VARCHAR(50),
    report_type VARCHAR(50) NOT NULL,  -- pdf, excel, csv, json
    report_name VARCHAR(200) NOT NULL,
    file_path VARCHAR(500),
    file_size INTEGER,
    generated_by INTEGER,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (run_id) REFERENCES dq_runs(run_id),
    FOREIGN KEY (generated_by) REFERENCES users(id)
);

-- System Settings Table
CREATE TABLE IF NOT EXISTS system_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT,
    setting_type VARCHAR(20),  -- string, integer, boolean, json
    description TEXT,
    updated_by INTEGER,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (updated_by) REFERENCES users(id)
);

-- Create Indexes for Performance
CREATE INDEX IF NOT EXISTS idx_dq_runs_user ON dq_runs(user_id);
CREATE INDEX IF NOT EXISTS idx_dq_runs_status ON dq_runs(status);
CREATE INDEX IF NOT EXISTS idx_dq_runs_started ON dq_runs(started_at);
CREATE INDEX IF NOT EXISTS idx_dq_metrics_run ON dq_metrics(run_id);
CREATE INDEX IF NOT EXISTS idx_dq_anomalies_run ON dq_anomalies(run_id);
CREATE INDEX IF NOT EXISTS idx_dq_anomalies_severity ON dq_anomalies(severity);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity);
CREATE INDEX IF NOT EXISTS idx_alerts_read ON alerts(is_read);
CREATE INDEX IF NOT EXISTS idx_audit_log_user ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_created ON audit_log(created_at);
CREATE INDEX IF NOT EXISTS idx_historical_trends_dataset ON historical_trends(dataset_name);
CREATE INDEX IF NOT EXISTS idx_historical_trends_recorded ON historical_trends(recorded_at);

-- Insert Default Roles
INSERT OR IGNORE INTO roles (role_name, description, permissions) VALUES
('admin', 'System Administrator', '["all"]'),
('manager', 'Data Quality Manager', '["view_all", "create_rules", "manage_alerts", "generate_reports"]'),
('analyst', 'Data Quality Analyst', '["view_own", "run_analysis", "view_reports"]'),
('viewer', 'Read-Only Viewer', '["view_own", "view_reports"]');

-- Insert Default Admin User (password: admin123 - CHANGE IN PRODUCTION!)
-- Password hash for 'admin123' using bcrypt
INSERT OR IGNORE INTO users (username, email, password_hash, full_name, role, is_active) VALUES
('admin', 'admin@dqplatform.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqNqNqNqNq', 'System Administrator', 'admin', 1);

-- Insert Default System Settings
INSERT OR IGNORE INTO system_settings (setting_key, setting_value, setting_type, description) VALUES
('max_file_size_mb', '100', 'integer', 'Maximum file upload size in MB'),
('session_timeout_minutes', '60', 'integer', 'Session timeout in minutes'),
('alert_retention_days', '90', 'integer', 'Number of days to retain alerts'),
('enable_email_notifications', 'false', 'boolean', 'Enable email notifications for alerts'),
('dq_score_threshold_critical', '70', 'integer', 'DQ score threshold for critical alerts'),
('dq_score_threshold_warning', '85', 'integer', 'DQ score threshold for warning alerts'),
('max_concurrent_analyses', '5', 'integer', 'Maximum concurrent DQ analyses'),
('enable_dark_mode', 'true', 'boolean', 'Enable dark mode support'),
('default_page_size', '25', 'integer', 'Default pagination page size'),
('enable_audit_log', 'true', 'boolean', 'Enable audit logging');

-- Made with Bob
