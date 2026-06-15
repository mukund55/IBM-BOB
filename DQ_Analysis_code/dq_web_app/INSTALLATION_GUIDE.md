# Enterprise Data Quality Platform - Installation Guide

## Overview
Complete enterprise web application for data quality management with modern UI, REST APIs, and integration with the existing DQ engine.

## Project Structure
```
dq_web_app/
├── app.py                      # Main Flask application
├── requirements.txt            # Python dependencies
├── config/
│   └── config.py              # Configuration settings
├── models/
│   └── models.py              # Database models (SQLAlchemy)
├── api/                       # REST API endpoints
│   ├── __init__.py
│   ├── auth.py               # Authentication & authorization
│   ├── analysis.py           # DQ analysis endpoints
│   ├── rules.py              # Business rules management
│   ├── alerts.py             # Alert management
│   ├── reports.py            # Report generation
│   ├── metadata.py           # Metadata catalog
│   ├── trends.py             # Historical trends
│   ├── reconciliation.py     # Data reconciliation
│   └── admin.py              # Administration
├── templates/                 # HTML templates
│   ├── base.html             # Base template with Bootstrap 5
│   ├── auth/                 # Authentication pages
│   ├── dashboard.html        # Main dashboard
│   ├── upload.html           # Upload & analyze
│   ├── results.html          # Analysis results
│   ├── rules.html            # Rule management
│   ├── alerts.html           # Alert center
│   ├── metadata.html         # Metadata catalog
│   ├── reports.html          # Reports
│   ├── reconciliation.html   # Reconciliation
│   ├── trends.html           # Historical trends
│   └── admin.html            # Administration
├── static/                    # Static assets
│   ├── css/
│   │   ├── main.css          # Main stylesheet
│   │   └── dark-mode.css     # Dark mode theme
│   ├── js/
│   │   ├── main.js           # Main JavaScript
│   │   ├── charts.js         # Chart.js visualizations
│   │   ├── upload.js         # File upload with drag-and-drop
│   │   └── dark-mode.js      # Dark mode toggle
│   └── img/                  # Images and icons
├── database/
│   ├── schema.sql            # Database schema
│   └── dq_platform.db        # SQLite database (created on init)
├── uploads/                   # Uploaded files
├── reports/                   # Generated reports
└── logs/                      # Application logs
```

## Installation Steps

### 1. Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Git (optional)

### 2. Create Virtual Environment
```bash
cd DQ_Analysis_code/dq_web_app
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Initialize Database
```bash
# The database will be automatically created on first run
# Or manually initialize:
python
>>> from app import create_app, init_db
>>> app = create_app()
>>> init_db(app)
>>> exit()
```

### 5. Configure Environment Variables (Optional)
Create a `.env` file:
```env
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///database/dq_platform.db
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-password
```

### 6. Run the Application
```bash
python app.py
```

The application will be available at: http://localhost:5000

### 7. Default Login Credentials
```
Username: admin
Password: admin123
```
**⚠️ IMPORTANT: Change the default password immediately after first login!**

## Features

### 1. Dashboard
- Total files processed
- Average DQ score
- Failed files count
- Active rules count
- Critical alerts
- Recent activity

### 2. Upload & Analyze
- Drag-and-drop file upload
- Support for CSV, XLSX, TXT, DAT, JSON, XML
- Real-time analysis progress
- Automatic DQ scoring

### 3. Results
- DQ score gauge
- Profiling metrics (15+ per column)
- Root cause analysis
- AI-powered recommendations
- Rule violations
- Interactive charts (Chart.js)

### 4. Rule Management
- Create/Edit/Delete business rules
- Rule categories (pattern, range, mandatory, custom)
- Rule versioning
- Severity levels
- Activation/deactivation

### 5. Alert Center
- Critical, high, medium, low alerts
- Alert filtering and search
- Mark as read/resolved
- Assignment to users
- Notification history

### 6. Metadata Catalog
- Auto-generated data dictionary
- Column statistics
- Semantic type inference
- Business definitions
- Metadata search

### 7. Reports
- PDF download
- Excel download
- CSV download
- JSON export
- Scheduled reports (optional)

### 8. Reconciliation
- Source vs Target comparison
- Count validation
- Hash validation
- Missing records detection
- Mismatch analysis

### 9. Historical Trends
- DQ score trends
- Duplicate trends
- Null value trends
- Anomaly trends
- Time-series charts

### 10. Administration
- User management
- Role-based access control (RBAC)
- Audit logs
- System settings
- Database management

## Security Features

### Authentication
- Secure password hashing (bcrypt)
- Session management
- Account lockout after failed attempts
- Password strength requirements

### Authorization
- Role-based access control (RBAC)
- Four roles: Admin, Manager, Analyst, Viewer
- Permission-based access to features

### Security Measures
- CSRF protection
- Input sanitization
- Secure file upload validation
- SQL injection prevention (SQLAlchemy ORM)
- XSS protection
- Audit logging

## API Documentation

### Authentication Endpoints
```
POST   /auth/login              - User login
GET    /auth/logout             - User logout
POST   /auth/register           - User registration
POST   /auth/change-password    - Change password
GET    /auth/profile            - View profile
POST   /auth/profile            - Update profile
```

### Analysis Endpoints
```
POST   /api/analysis/upload     - Upload file for analysis
POST   /api/analysis/run        - Run DQ analysis
GET    /api/analysis/status/:id - Get analysis status
GET    /api/analysis/results/:id - Get analysis results
GET    /api/analysis/list       - List all analyses
DELETE /api/analysis/:id        - Delete analysis
```

### Rules Endpoints
```
GET    /api/rules               - List all rules
POST   /api/rules               - Create new rule
GET    /api/rules/:id           - Get rule details
PUT    /api/rules/:id           - Update rule
DELETE /api/rules/:id           - Delete rule
POST   /api/rules/:id/activate  - Activate rule
POST   /api/rules/:id/deactivate - Deactivate rule
```

### Alerts Endpoints
```
GET    /api/alerts              - List all alerts
GET    /api/alerts/:id          - Get alert details
POST   /api/alerts/:id/read     - Mark as read
POST   /api/alerts/:id/resolve  - Resolve alert
POST   /api/alerts/:id/assign   - Assign to user
```

### Reports Endpoints
```
GET    /api/reports             - List all reports
POST   /api/reports/generate    - Generate report
GET    /api/reports/:id/download - Download report
DELETE /api/reports/:id         - Delete report
```

## Technology Stack

### Backend
- **Framework**: Flask 3.0
- **ORM**: SQLAlchemy 2.0
- **Authentication**: Flask-Login
- **Database**: SQLite (default), PostgreSQL, Oracle supported

### Frontend
- **UI Framework**: Bootstrap 5
- **Charts**: Chart.js
- **Icons**: Font Awesome
- **JavaScript**: Vanilla JS (ES6+)

### Security
- **Password Hashing**: bcrypt
- **CSRF Protection**: Flask-WTF
- **Session Management**: Flask-Login

## Configuration

### Development
```python
FLASK_ENV=development
DEBUG=True
```

### Production
```python
FLASK_ENV=production
DEBUG=False
SECRET_KEY=<strong-random-key>
DATABASE_URL=postgresql://user:pass@host/db
```

## Deployment

### Using Gunicorn (Production)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Using Docker
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

## Troubleshooting

### Database Issues
```bash
# Reset database
rm database/dq_platform.db
python app.py  # Will recreate
```

### Permission Issues
```bash
# Ensure proper permissions
chmod -R 755 uploads/
chmod -R 755 reports/
chmod -R 755 logs/
```

### Port Already in Use
```bash
# Change port in app.py or use environment variable
export FLASK_RUN_PORT=8000
python app.py
```

## Support

For issues or questions:
1. Check the logs in `logs/dq_platform.log`
2. Review the audit log in the database
3. Check the API documentation
4. Contact the development team

## License

Enterprise Data Quality Platform
Copyright © 2026 - All Rights Reserved

## Version History

- **v1.0.0** (2026-06-15)
  - Initial release
  - Complete web application
  - REST API
  - Modern UI with Bootstrap 5
  - Integration with DQ engine
  - RBAC and security features