@echo off
REM ============================================================================
REM Quick Setup Script for Oracle Database Integration
REM ============================================================================

echo.
echo ============================================================================
echo Oracle Database Quick Setup for Data Quality Analysis
echo ============================================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python from https://www.python.org/
    pause
    exit /b 1
)

echo [OK] Python is installed

REM Install cx_Oracle
echo.
echo ============================================================================
echo Installing cx_Oracle package...
echo ============================================================================
pip install cx_Oracle
if errorlevel 1 (
    echo [ERROR] Failed to install cx_Oracle
    pause
    exit /b 1
)

echo [OK] cx_Oracle installed successfully

REM Check if Oracle Instant Client is in PATH
echo.
echo ============================================================================
echo Checking Oracle Instant Client...
echo ============================================================================

where oci.dll >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Oracle Instant Client not found in PATH
    echo.
    echo Please download and install Oracle Instant Client:
    echo 1. Visit: https://www.oracle.com/database/technologies/instant-client/downloads.html
    echo 2. Download "Basic Package" for Windows x64
    echo 3. Extract to C:\oracle\instantclient_21_9
    echo 4. Add to PATH: C:\oracle\instantclient_21_9
    echo.
    echo After installation, run this script again.
    pause
    exit /b 1
) else (
    echo [OK] Oracle Instant Client found
)

REM Test Oracle connection
echo.
echo ============================================================================
echo Testing Oracle Database Connection...
echo ============================================================================
python test_oracle_connection.py
if errorlevel 1 (
    echo.
    echo [ERROR] Oracle connection test failed
    echo.
    echo Please ensure:
    echo 1. Oracle Database is installed and running
    echo 2. Connection details in dq_config_oracle.json are correct
    echo 3. Test user 'dq_test' exists with password 'dq_test123'
    echo.
    echo To create the test user and data, run:
    echo   sqlplus sys/your_password@localhost:1521/XE as sysdba @setup_oracle_db.sql
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================================================
echo Setup Complete!
echo ============================================================================
echo.
echo You can now run data quality analysis on Oracle database:
echo.
echo   python data_quality_analysis.py --use-database --config-file dq_config_oracle.json
echo.
echo Or with dashboard:
echo.
echo   python data_quality_analysis.py --use-database --config-file dq_config_oracle.json --generate-dashboard
echo.
echo ============================================================================
pause

@REM Made with Bob
