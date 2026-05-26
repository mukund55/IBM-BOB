@echo off
REM Data Quality Analysis Runner Script
REM This script runs the data quality analysis from the correct directory

echo ========================================
echo Data Quality Analysis Tool
echo ========================================
echo.

REM Change to the script directory
cd /d "%~dp0"

echo Current Directory: %CD%
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7 or higher
    pause
    exit /b 1
)

echo Python found!
echo.

REM Check if required packages are installed
echo Checking required packages...
python -c "import pandas, numpy" >nul 2>&1
if errorlevel 1 (
    echo WARNING: Required packages not found
    echo Installing pandas and numpy...
    pip install pandas numpy openpyxl
)

echo.
echo Running Data Quality Analysis...
echo ========================================
echo.

REM Run the analysis with sample data
python data_quality_analysis.py --input-file sample_customer_data.csv

echo.
echo ========================================
echo Analysis Complete!
echo Check the dq_output folder for results
echo ========================================
pause

@REM Made with Bob
