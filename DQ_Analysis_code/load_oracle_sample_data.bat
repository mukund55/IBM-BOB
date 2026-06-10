@echo off
REM ============================================================================
REM Load Sample Data into Oracle Database for DQ Analysis Testing
REM ============================================================================
REM
REM This script loads comprehensive sample data (good + bad quality) into
REM Oracle database for testing the DQ analysis tool.
REM
REM Prerequisites:
REM   1. Oracle database running (docker container or local)
REM   2. User 'dq_test' created (run setup_oracle_db.sql first if needed)
REM
REM ============================================================================

echo.
echo ============================================================================
echo Load Oracle Sample Data for DQ Analysis
echo ============================================================================
echo.

REM Check if Oracle container is running
docker ps | findstr oracle-xe >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Oracle container is not running
    echo.
    echo Please start it with:
    echo   docker start oracle-xe
    echo.
    echo Or create a new container:
    echo   docker run -d --name oracle-xe -p 1521:1521 -e ORACLE_PASSWORD=Oracle123 gvenzl/oracle-xe:latest
    echo.
    pause
    exit /b 1
)

echo [OK] Oracle container is running

REM Wait for database to be ready
echo.
echo Checking if database is ready...
timeout /t 3 /nobreak >nul

docker logs oracle-xe 2>&1 | findstr "DATABASE IS READY TO USE" >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Database may not be fully ready yet
    echo Waiting 30 seconds...
    timeout /t 30 /nobreak
)

echo [OK] Database is ready

REM Copy SQL script to container
echo.
echo ============================================================================
echo Copying SQL script to container...
echo ============================================================================
docker cp DQ_Analysis_code\setup_oracle_dq_sample_data.sql oracle-xe:/tmp/
if errorlevel 1 (
    echo [ERROR] Failed to copy SQL script
    pause
    exit /b 1
)
echo [OK] SQL script copied

REM Execute SQL script
echo.
echo ============================================================================
echo Loading sample data into Oracle database...
echo ============================================================================
echo.
echo This will create table 'customer_data' with 55 records:
echo   - 20 good quality records
echo   - 10 records with NULL/missing values
echo   - 10 records with invalid formats
echo   - 10 records with outliers and anomalies
echo   - 5 duplicate records
echo.

docker exec -it oracle-xe sqlplus -S dq_test/dq_test123@XE @/tmp/setup_oracle_dq_sample_data.sql

if errorlevel 1 (
    echo.
    echo [WARNING] SQL script execution may have had issues
    echo Please check the output above
    echo.
    echo If user 'dq_test' doesn't exist, run setup_oracle_db.sql first:
    echo   docker exec -it oracle-xe sqlplus sys/Oracle123@XE as sysdba @/tmp/setup_oracle_db.sql
    pause
    exit /b 1
)

echo.
echo ============================================================================
echo Sample Data Loaded Successfully!
echo ============================================================================
echo.
echo Table: customer_data
echo Total Records: 55
echo.
echo Data Quality Breakdown:
echo   ✓ Good Quality: 20 records (36%%)
echo   ✗ NULL/Missing: 10 records (18%%)
echo   ✗ Invalid Formats: 10 records (18%%)
echo   ✗ Outliers: 10 records (18%%)
echo   ✗ Duplicates: 5 records (9%%)
echo.
echo ============================================================================
echo Next Steps:
echo ============================================================================
echo.
echo 1. Test the connection:
echo    python DQ_Analysis_code\test_oracle_dq_connection.py
echo.
echo 2. Run DQ Analysis:
echo    DQ_Analysis_code\run_oracle_dq_analysis.bat
echo.
echo 3. Or run manually:
echo    python DQ_Analysis_code\data_quality_analysis.py --use-database --config-file DQ_Analysis_code\oracle_connection_config.json --generate-dashboard
echo.
echo ============================================================================

pause

@REM Made with Bob
