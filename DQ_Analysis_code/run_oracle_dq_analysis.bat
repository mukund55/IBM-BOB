@echo off
REM ============================================================================
REM Run Data Quality Analysis with Oracle Database
REM ============================================================================
REM
REM This script runs the DQ analysis tool against Oracle database
REM using the oracle_connection_config.json configuration file.
REM
REM Prerequisites:
REM   1. Oracle database running (docker container or local)
REM   2. cx_Oracle installed (pip install cx_Oracle)
REM   3. SQLAlchemy installed (pip install sqlalchemy)
REM   4. Oracle Instant Client installed
REM   5. Database setup completed (run setup_oracle_db.sql)
REM
REM ============================================================================

echo.
echo ============================================================================
echo Data Quality Analysis - Oracle Database
echo ============================================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.7 or higher
    pause
    exit /b 1
)

echo [OK] Python is available

REM Check if configuration file exists
if not exist "DQ_Analysis_code\oracle_connection_config.json" (
    echo [ERROR] Configuration file not found: oracle_connection_config.json
    echo Please ensure the file exists in DQ_Analysis_code directory
    pause
    exit /b 1
)

echo [OK] Configuration file found

REM Check if DQ analysis script exists
if not exist "DQ_Analysis_code\data_quality_analysis.py" (
    echo [ERROR] DQ analysis script not found: data_quality_analysis.py
    echo Please ensure the file exists in DQ_Analysis_code directory
    pause
    exit /b 1
)

echo [OK] DQ analysis script found

REM Test Oracle connection first
echo.
echo ============================================================================
echo Testing Oracle Connection...
echo ============================================================================
echo.

python DQ_Analysis_code\test_oracle_dq_connection.py --config DQ_Analysis_code\oracle_connection_config.json
if errorlevel 1 (
    echo.
    echo [ERROR] Oracle connection test failed
    echo Please fix the connection issues before running DQ analysis
    pause
    exit /b 1
)

echo.
echo [OK] Oracle connection test passed

REM Run DQ Analysis
echo.
echo ============================================================================
echo Running Data Quality Analysis...
echo ============================================================================
echo.

python DQ_Analysis_code\data_quality_analysis.py ^
    --use-database ^
    --config-file DQ_Analysis_code\oracle_connection_config.json ^
    --generate-dashboard

if errorlevel 1 (
    echo.
    echo [ERROR] DQ analysis failed
    echo Check the log file for details: dq_output_oracle_test\dq_oracle_run.log
    pause
    exit /b 1
)

echo.
echo ============================================================================
echo DQ Analysis Complete!
echo ============================================================================
echo.
echo Output directory: dq_output_oracle_test
echo.
echo Key files:
echo   - dq_executive_dashboard.html  (Open in browser)
echo   - dq_executive_summary.txt     (Quick summary)
echo   - dq_summary.csv               (Detailed metrics)
echo   - good_records.csv             (Clean data)
echo   - dq_all_bad_records.csv       (Issues found)
echo   - dq_oracle_run.log            (Execution log)
echo.
echo ============================================================================

REM Open dashboard in browser
if exist "dq_output_oracle_test\dq_executive_dashboard.html" (
    echo.
    echo Opening dashboard in browser...
    start dq_output_oracle_test\dq_executive_dashboard.html
)

pause

@REM Made with Bob
