@echo off
echo ========================================
echo Ab Initio Code Analyzer Web Application
echo ========================================
echo.

REM Check if Flask is installed
python -c "import flask" 2>nul
if errorlevel 1 (
    echo Flask is not installed. Installing dependencies...
    pip install -r requirements_web.txt
    echo.
)

echo Starting web server...
echo.
echo Open your browser and navigate to:
echo http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo.

python web_analyzer_app.py

pause

@REM Made with Bob
