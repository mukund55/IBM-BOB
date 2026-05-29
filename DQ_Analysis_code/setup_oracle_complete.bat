@echo off
REM ============================================================================
REM Complete Oracle Database Setup Script for DQ Analysis
REM ============================================================================

echo.
echo ============================================================================
echo Oracle Database Complete Setup for Data Quality Analysis
echo ============================================================================
echo.

REM Check if container is running
docker ps | findstr oracle-xe >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Oracle container is not running
    echo Please start it with: docker start oracle-xe
    pause
    exit /b 1
)

echo [OK] Oracle container is running

REM Wait for database to be ready
echo.
echo ============================================================================
echo Waiting for Oracle Database to be ready (this may take 2-3 minutes)...
echo ============================================================================
echo.

:wait_loop
timeout /t 10 /nobreak >nul
docker logs oracle-xe 2>&1 | findstr "DATABASE IS READY TO USE" >nul 2>&1
if errorlevel 1 (
    echo Still waiting... (checking every 10 seconds)
    goto wait_loop
)

echo.
echo [OK] Oracle Database is ready!

REM Copy SQL setup script to container
echo.
echo ============================================================================
echo Copying SQL setup script to container...
echo ============================================================================
docker cp DQ_Analysis_code/setup_oracle_db.sql oracle-xe:/tmp/
if errorlevel 1 (
    echo [ERROR] Failed to copy SQL script
    pause
    exit /b 1
)
echo [OK] SQL script copied

REM Execute SQL script
echo.
echo ============================================================================
echo Creating database schema and test data...
echo ============================================================================
docker exec -it oracle-xe sqlplus -S sys/Oracle123@XE as sysdba @/tmp/setup_oracle_db.sql
if errorlevel 1 (
    echo [WARNING] SQL script execution may have had issues
    echo Please check the output above
)

echo.
echo [OK] Database setup complete

REM Install Python dependencies
echo.
echo ============================================================================
echo Installing Python dependencies...
echo ============================================================================
pip install cx_Oracle >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Failed to install cx_Oracle
    echo Please run: pip install cx_Oracle
) else (
    echo [OK] cx_Oracle installed
)

REM Create Oracle configuration file
echo.
echo ============================================================================
echo Creating Oracle DQ configuration file...
echo ============================================================================

(
echo {
echo   "general": {
echo     "output_dir": "dq_output_oracle",
echo     "log_file": "dq_run.log"
echo   },
echo   "database": {
echo     "type": "oracle",
echo     "host": "localhost",
echo     "port": 1521,
echo     "service_name": "XE",
echo     "username": "dq_test",
echo     "password": "dq_test123",
echo     "query": "SELECT * FROM customers"
echo   },
echo   "rules": {
echo     "mandatory_columns": ["customer_id", "customer_name", "email"],
echo     "email_columns": ["email"],
echo     "primary_key": ["customer_id"]
echo   }
echo }
) > DQ_Analysis_code\dq_config_oracle.json

echo [OK] Configuration file created: dq_config_oracle.json

echo.
echo ============================================================================
echo Setup Complete!
echo ============================================================================
echo.
echo Connection Details:
echo   Host: localhost
echo   Port: 1521
echo   Service: XE
echo   Username: dq_test
echo   Password: dq_test123
echo.
echo Next Steps:
echo.
echo 1. Test the connection:
echo    python DQ_Analysis_code/test_oracle_connection.py
echo.
echo 2. Run data quality analysis:
echo    python DQ_Analysis_code/data_quality_analysis.py --use-database --config-file DQ_Analysis_code/dq_config_oracle.json
echo.
echo 3. Generate dashboard:
echo    python DQ_Analysis_code/data_quality_analysis.py --use-database --config-file DQ_Analysis_code/dq_config_oracle.json --generate-dashboard
echo.
echo ============================================================================
pause

@REM Made with Bob
