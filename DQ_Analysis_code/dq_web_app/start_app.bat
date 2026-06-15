@echo off
echo ========================================
echo  Data Quality Web Application Launcher
echo ========================================
echo.

cd /d "%~dp0"

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo [1/5] Checking virtual environment...
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created successfully!
) else (
    echo Virtual environment already exists.
)

echo.
echo [2/5] Activating virtual environment...
call venv\Scripts\activate
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

echo.
echo [3/5] Checking dependencies...
if not exist venv\Lib\site-packages\flask (
    echo Installing dependencies (this may take 5-10 minutes)...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
    echo Dependencies installed successfully!
) else (
    echo Dependencies already installed.
)

echo.
echo [4/5] Checking database...
if not exist dq_webapp.db (
    echo Initializing database...
    python init_db.py
    if errorlevel 1 (
        echo ERROR: Failed to initialize database
        pause
        exit /b 1
    )
    echo Database initialized successfully!
    echo.
    echo DEFAULT LOGIN CREDENTIALS:
    echo Username: admin
    echo Password: admin123
    echo.
) else (
    echo Database already exists.
)

echo.
echo [5/5] Starting Flask application...
echo.
echo ========================================
echo  Application is starting...
echo  URL: http://localhost:5000/dashboard
echo  Press Ctrl+C to stop the server
echo ========================================
echo.

python app.py

pause

@REM Made with Bob
