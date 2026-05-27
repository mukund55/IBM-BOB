@echo off
REM ============================================================================
REM PostgreSQL Setup and Test Script for Windows
REM ============================================================================
REM This script sets up PostgreSQL with Docker and runs DQ analysis
REM Run this from the DQ_Analysis_code directory
REM ============================================================================

echo.
echo ================================================================================
echo PostgreSQL Setup for Data Quality Analysis
echo ================================================================================
echo.

REM Check if Docker is installed
echo [1/6] Checking Docker installation...
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not installed or not running
    echo.
    echo Please install Docker Desktop from:
    echo https://www.docker.com/products/docker-desktop
    echo.
    pause
    exit /b 1
)
echo [OK] Docker is installed
echo.

REM Check if PostgreSQL container already exists
echo [2/6] Checking for existing PostgreSQL container...
docker inspect postgres-dq >nul 2>&1
if errorlevel 1 (
    echo [INFO] Creating new PostgreSQL container...
    docker run -d --name postgres-dq -e POSTGRES_PASSWORD=postgres123 -e POSTGRES_USER=dq_user -e POSTGRES_DB=dq_test -p 5432:5432 postgres:15
    if errorlevel 1 (
        echo [ERROR] Failed to create PostgreSQL container
        pause
        exit /b 1
    )
    echo [OK] PostgreSQL container created
    echo [INFO] Waiting for PostgreSQL to start 15 seconds...
    timeout /t 15 /nobreak >nul
) else (
    echo [INFO] PostgreSQL container already exists
    echo [INFO] Starting container...
    docker start postgres-dq >nul 2>&1
    timeout /t 5 /nobreak >nul
)
echo [OK] PostgreSQL is ready
echo.

REM Install Python driver
echo [3/6] Installing PostgreSQL Python driver...
pip install psycopg2-binary >nul 2>&1
if errorlevel 1 (
    echo [WARN] Failed to install psycopg2-binary, trying alternative...
    pip install psycopg2-binary --no-cache-dir
)
echo [OK] Python driver installed
echo.

REM Create test data
echo [4/6] Creating test data in PostgreSQL...
docker cp setup_postgres_data.sql postgres-dq:/tmp/setup_postgres_data.sql
docker exec -i postgres-dq psql -U dq_user -d dq_test -f /tmp/setup_postgres_data.sql

if errorlevel 1 (
    echo [ERROR] Failed to create test data
    echo [INFO] Container might still be starting. Wait a moment and try again.
    pause
    exit /b 1
)
echo [OK] Test data created (6 records with quality issues)
echo.

REM Test connection
echo [5/6] Testing database connection...
python test_database_integration.py
echo.

REM Run DQ Analysis
echo [6/6] Running Data Quality Analysis...
echo.
echo Command: python data_quality_analysis.py --use-database --config-file dq_config_postgres.json --generate-dashboard --cleanse-data
echo.
python data_quality_analysis.py --use-database --config-file dq_config_postgres.json --generate-dashboard --cleanse-data

if errorlevel 1 (
    echo.
    echo [ERROR] DQ Analysis failed
    echo.
    echo Troubleshooting:
    echo 1. Check if PostgreSQL is running: docker ps
    echo 2. Check logs: docker logs postgres-dq
    echo 3. Test connection: python test_database_integration.py
    echo.
    pause
    exit /b 1
)

echo.
echo ================================================================================
echo SUCCESS! Data Quality Analysis Complete
echo ================================================================================
echo.
echo Output files created in: dq_output_postgres\
echo.
echo Key files:
echo   - dq_executive_dashboard.html  (Open this in browser)
echo   - cleansed_data.csv            (Cleaned data)
echo   - dq_cleansing_log.csv         (Cleansing operations)
echo   - bad_records_*.csv            (Issues by category)
echo.
echo To view the dashboard:
echo   start dq_output_postgres\dq_executive_dashboard.html
echo.
echo To stop PostgreSQL:
echo   docker stop postgres-dq
echo.
echo To restart PostgreSQL later:
echo   docker start postgres-dq
echo.
echo ================================================================================
pause

@REM Made with Bob
