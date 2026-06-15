# Data Quality Analysis Web Application - Setup Guide

## 📋 Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Detailed Installation Steps](#detailed-installation-steps)
- [Running the Application](#running-the-application)
- [Default Login Credentials](#default-login-credentials)
- [Using the Application](#using-the-application)
- [Troubleshooting](#troubleshooting)
- [Project Structure](#project-structure)

---

## 🎯 Overview

Enterprise-grade Data Quality Analysis web application for analyzing data files and generating comprehensive quality reports.

**Access URL**: `http://localhost:5000/dashboard`

**Supported File Types**: CSV, Excel (.xlsx, .xls), JSON, XML, DAT (up to 100MB)

---

## ✅ Prerequisites

### Required Software
1. **Python 3.8+** - [Download](https://www.python.org/downloads/)
   ```bash
   python --version  # Verify installation
   ```

2. **pip** (comes with Python)
   ```bash
   pip --version
   ```

### System Requirements
- **OS**: Windows 10/11, macOS, Linux
- **RAM**: 4GB minimum (8GB recommended)
- **Disk**: 500MB free space
- **Browser**: Chrome, Firefox, Edge, Safari (latest)

---

## 🚀 Quick Start

### Windows (PowerShell/CMD)

```powershell
# Navigate to project
cd path\to\DQ_Analysis_code\dq_web_app

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python init_db.py

# Run application
python app.py
```

### macOS/Linux (Terminal)

```bash
# Navigate to project
cd path/to/DQ_Analysis_code/dq_web_app

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python init_db.py

# Run application
python app.py
```

### Using Batch File (Windows)

Create `start_app.bat` in `dq_web_app` folder:

```batch
@echo off
echo Starting Data Quality Web Application...
cd /d "%~dp0"

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate

if not exist dq_webapp.db (
    echo Installing dependencies...
    pip install -r requirements.txt
    echo Initializing database...
    python init_db.py
)

echo Starting Flask application...
python app.py
pause
```

Double-click `start_app.bat` to run!

---

## 📝 Detailed Installation Steps

### Step 1: Download the Project

Extract the project files to a location like:
- Windows: `C:\Projects\DQ_Analysis_code`
- macOS/Linux: `~/Projects/DQ_Analysis_code`

### Step 2: Open Terminal/Command Prompt

**Windows**: 
- Press `Win + R`, type `cmd` or `powershell`, press Enter
- Navigate: `cd C:\Projects\DQ_Analysis_code\dq_web_app`

**macOS/Linux**:
- Open Terminal application
- Navigate: `cd ~/Projects/DQ_Analysis_code/dq_web_app`

### Step 3: Create Virtual Environment

```bash
python -m venv venv
```

This creates a `venv` folder with isolated Python environment.

### Step 4: Activate Virtual Environment

**Windows**:
```powershell
.\venv\Scripts\activate
```

**macOS/Linux**:
```bash
source venv/bin/activate
```

You'll see `(venv)` prefix in your prompt.

### Step 5: Install Dependencies

```bash
pip install -r requirements.txt
```

**Time**: 5-10 minutes depending on internet speed.

**Packages installed**: Flask, SQLAlchemy, Pandas, Matplotlib, Plotly, and 60+ others.

### Step 6: Initialize Database

```bash
python init_db.py
```

**Creates**:
- `dq_webapp.db` - SQLite database
- Admin user account
- Required tables

**Output**:
```
Database initialized successfully!
Admin user created: admin / admin123
```

### Step 7: Verify Setup

Check these exist:
```
dq_web_app/
├── venv/              ✓ Virtual environment
├── dq_webapp.db       ✓ Database (after init_db.py)
├── app.py             ✓ Main application
├── requirements.txt   ✓ Dependencies list
├── uploads/           ✓ Upload directory
├── dq_output/         ✓ Output directory
└── templates/         ✓ HTML templates
```

---

## 🎮 Running the Application

### Start the Server

```bash
python app.py
```

**Expected Output**:
```
 * Serving Flask app 'app'
 * Debug mode: on
WARNING: This is a development server. Do not use it in production.
 * Running on http://127.0.0.1:5000
Press CTRL+C to quit
```

### Access the Application

1. Open your browser
2. Go to: `http://localhost:5000/dashboard`
3. You'll be redirected to login page

### Stop the Server

Press `Ctrl + C` in the terminal

---

## 🔐 Default Login Credentials

**Username**: `admin`  
**Password**: `admin123`

**⚠️ IMPORTANT**: Change the password after first login!

To change password:
1. Login with default credentials
2. Go to Profile/Settings
3. Update password

---

## 📊 Using the Application

### 1. Login
- Navigate to `http://localhost:5000/dashboard`
- Enter credentials: `admin` / `admin123`
- Click "Login"

### 2. Upload Data File
- Click "Drop your file here or click to browse"
- Select a file (CSV, Excel, JSON, XML, DAT)
- File uploads automatically

### 3. Analyze Data
- Click "Analyze Data Quality" button
- Wait for analysis to complete (10-30 seconds)
- View results page with summary statistics

### 4. View Reports

**Dashboard Cards**:
- **Anomaly Report** - View data quality issues with severity levels
- **Cleansed Data** - Download good records
- **Visual Reports** - View charts and visualizations
- **Smart Recommendations** - Get improvement suggestions

### 5. Download Results
- Click download buttons on each report page
- Files saved to your Downloads folder

---

## 🔧 Troubleshooting

### Issue: "Python not found"
**Solution**: 
- Install Python from python.org
- Add Python to PATH during installation
- Restart terminal after installation

### Issue: "pip not found"
**Solution**:
```bash
python -m ensurepip --upgrade
```

### Issue: "Permission denied" (macOS/Linux)
**Solution**:
```bash
chmod +x app.py
# Or use sudo for pip install
sudo pip install -r requirements.txt
```

### Issue: "Port 5000 already in use"
**Solution**:
```bash
# Find process using port 5000
# Windows:
netstat -ano | findstr :5000
taskkill /PID <process_id> /F

# macOS/Linux:
lsof -i :5000
kill -9 <process_id>
```

Or change port in `app.py`:
```python
app.run(debug=True, port=5001)  # Use port 5001 instead
```

### Issue: "Module not found" errors
**Solution**:
```bash
# Ensure virtual environment is activated
# Windows:
.\venv\Scripts\activate

# macOS/Linux:
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: Database errors
**Solution**:
```bash
# Delete and recreate database
rm dq_webapp.db  # macOS/Linux
del dq_webapp.db  # Windows

# Reinitialize
python init_db.py
```

### Issue: Upload fails
**Solution**:
- Check file size (max 100MB)
- Ensure `uploads/` folder exists
- Check file format is supported
- Verify file is not corrupted

### Issue: Analysis takes too long
**Solution**:
- Large files (>50MB) may take 1-2 minutes
- Check terminal for progress logs
- Ensure sufficient RAM available
- Try with smaller file first

---

## 📁 Project Structure

```
DQ_Analysis_code/
└── dq_web_app/
    ├── app.py                    # Main Flask application
    ├── init_db.py               # Database initialization
    ├── requirements.txt         # Python dependencies
    ├── SETUP_GUIDE.md          # This file
    │
    ├── api/                     # API endpoints
    │   ├── __init__.py
    │   ├── auth.py             # Authentication routes
    │   └── analysis.py         # Analysis routes
    │
    ├── config/                  # Configuration
    │   ├── __init__.py
    │   └── config.py           # App configuration
    │
    ├── models/                  # Database models
    │   ├── __init__.py
    │   ├── user.py             # User model
    │   └── dq_run.py           # DQ run model
    │
    ├── templates/               # HTML templates
    │   ├── base.html           # Base template
    │   ├── dashboard.html      # Main dashboard
    │   ├── results.html        # Results page
    │   ├── anomaly_report.html # Anomaly report
    │   ├── cleansed_data.html  # Cleansed data
    │   ├── visual_reports.html # Visual reports
    │   └── recommendations.html # Recommendations
    │
    ├── static/                  # Static files
    │   ├── css/                # Stylesheets
    │   ├── js/                 # JavaScript
    │   └── images/             # Images
    │
    ├── uploads/                 # Uploaded files
    ├── dq_output/              # Analysis output
    ├── venv/                   # Virtual environment
    └── dq_webapp.db            # SQLite database
```

---

## 🚀 Next Steps

1. **Change Default Password**
   - Login and update admin password

2. **Test with Sample Data**
   - Use `customer_data_10k.csv` from parent directory
   - Upload and analyze

3. **Explore Features**
   - Try different file formats
   - View all report types
   - Download results

4. **Customize Configuration**
   - Edit `config/config.py` for custom settings
   - Adjust file size limits
   - Configure database

5. **Share with Team**
   - Share this SETUP_GUIDE.md
   - Share the entire `dq_web_app` folder
   - Team members follow same setup steps

---

## 📞 Support

For issues or questions:
1. Check Troubleshooting section above
2. Review terminal logs for error messages
3. Ensure all prerequisites are installed
4. Verify virtual environment is activated

---

## 📄 License

Enterprise Data Quality Analysis Tool  
© 2026 All Rights Reserved

---

**Happy Data Quality Analysis! 🎉**