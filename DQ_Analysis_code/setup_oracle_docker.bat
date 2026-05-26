@echo off
REM ============================================================================
REM Oracle Database Docker Setup Script
REM ============================================================================
REM This script sets up Oracle Database XE in Docker for data quality testing
REM ============================================================================

echo.
echo ============================================================================
echo Oracle Database Docker Setup for Data Quality Analysis
echo ============================================================================
echo.

REM Check if Docker is installed
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

REM Check if Docker is running
docker ps >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running
    echo.
    echo Please start Docker Desktop and try again
    echo.
    pause
    exit /b 1
)

echo [OK] Docker is running

REM Check if oracle-xe container already exists
docker ps -a | findstr oracle-xe >nul 2>&1
if not errorlevel 1 (
    echo.
    echo [INFO] Oracle XE container already exists
    echo.
    choice /C YN /M "Do you want to remove the existing container and create a new one"
    if errorlevel 2 goto skip_remove
    if errorlevel 1 goto remove_container
    
    :remove_container
    echo.
    echo Stopping and removing existing container...
    docker stop oracle-xe 2>nul
    docker rm oracle-xe 2>nul
    echo [OK] Existing container removed
    
    :skip_remove
)

REM Pull Oracle XE image
echo.
echo ============================================================================
echo Pulling Oracle Database XE 21c Image (this may take a few minutes)...
echo ============================================================================
echo.
docker pull container-registry.oracle.com/database/express:21.3.0-xe
if errorlevel 1 (
    echo [ERROR] Failed to pull Oracle XE image
    echo.
    echo Please check your internet connection and try again
    pause
    exit /b 1
)

echo [OK] Oracle XE image pulled successfully

REM Run Oracle XE container
echo.
echo ============================================================================
echo Starting Oracle Database XE Container...
echo ============================================================================
echo.
echo Container name: oracle-xe
echo Port: 1521
echo Password: Oracle123
echo.

docker run -d ^
  --name oracle-xe ^
  -p 1521:1521 ^
  -p 5500:5500 ^
  -e ORACLE_PWD=Oracle123 ^
  container-registry.oracle.com/database/express:21.3.0-xe

if errorlevel 1 (
    echo [ERROR] Failed to start Oracle XE container
    pause
    exit /b 1
)

echo [OK] Oracle XE container started

REM Wait for database to be ready
echo.
echo ============================================================================
echo Waiting for Oracle Database to be ready (this may take 2-3 minutes)...
echo ============================================================================
echo.
echo Please wait while the database initializes...
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

REM Display connection information
echo.
echo ============================================================================
echo Oracle Database Connection Information
echo ============================================================================
echo.
echo Host: localhost
echo Port: 1521
echo Service Name: XE
echo SYS Password: Oracle123
echo.
echo Enterprise Manager: http://localhost:5500/em
echo.

REM Install Python dependencies
echo.
echo ============================================================================
echo Installing Python Dependencies...
echo ============================================================================
echo.

pip install cx_Oracle >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Failed to install cx_Oracle
    echo Please run: pip install cx_Oracle
) else (
    echo [OK] cx_Oracle installed
)

REM Check for Oracle Instant Client
echo.
echo ============================================================================
echo Checking Oracle Instant Client...
echo ============================================================================
echo.

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
    echo After installation, continue with the next steps.
) else (
    echo [OK] Oracle Instant Client found
)

echo.
echo ============================================================================
echo Next Steps
echo ============================================================================
echo.
echo 1. Setup database schema and test data:
echo    docker exec -it oracle-xe sqlplus sys/Oracle123@XE as sysdba
echo    Then run: @setup_oracle_db.sql
echo.
echo 2. Or copy the SQL file into container and run:
echo    docker cp setup_oracle_db.sql oracle-xe:/tmp/
echo    docker exec -it oracle-xe sqlplus sys/Oracle123@XE as sysdba @/tmp/setup_oracle_db.sql
echo.
echo 3. Test the connection:
echo    python test_oracle_connection.py
echo.
echo 4. Run data quality analysis:
echo    python data_quality_analysis.py --use-database --config-file dq_config_oracle.json
echo.
echo ============================================================================
echo.
echo Container Management Commands:
echo   Start:   docker start oracle-xe
echo   Stop:    docker stop oracle-xe
echo   Logs:    docker logs -f oracle-xe
echo   Remove:  docker stop oracle-xe ^&^& docker rm oracle-xe
echo.
echo ============================================================================
echo.

pause

@REM Made with Bob
