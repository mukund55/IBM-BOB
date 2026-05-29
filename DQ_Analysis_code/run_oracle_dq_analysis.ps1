# ============================================================================
# Run Data Quality Analysis with Oracle Database (PowerShell)
# ============================================================================
#
# This script runs the DQ analysis tool against Oracle database
# using the oracle_connection_config.json configuration file.
#
# Prerequisites:
#   1. Oracle database running (docker container or local)
#   2. cx_Oracle installed (pip install cx_Oracle)
#   3. SQLAlchemy installed (pip install sqlalchemy)
#   4. Oracle Instant Client installed
#   5. Database setup completed (run setup_oracle_db.sql)
#
# ============================================================================

Write-Host ""
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "Data Quality Analysis - Oracle Database" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[OK] Python is available: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.7 or higher" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if configuration file exists
if (-not (Test-Path "DQ_Analysis_code\oracle_connection_config.json")) {
    Write-Host "[ERROR] Configuration file not found: oracle_connection_config.json" -ForegroundColor Red
    Write-Host "Please ensure the file exists in DQ_Analysis_code directory" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "[OK] Configuration file found" -ForegroundColor Green

# Check if DQ analysis script exists
if (-not (Test-Path "DQ_Analysis_code\data_quality_analysis.py")) {
    Write-Host "[ERROR] DQ analysis script not found: data_quality_analysis.py" -ForegroundColor Red
    Write-Host "Please ensure the file exists in DQ_Analysis_code directory" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "[OK] DQ analysis script found" -ForegroundColor Green

# Test Oracle connection first
Write-Host ""
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "Testing Oracle Connection..." -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""

python DQ_Analysis_code\test_oracle_dq_connection.py --config DQ_Analysis_code\oracle_connection_config.json

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[ERROR] Oracle connection test failed" -ForegroundColor Red
    Write-Host "Please fix the connection issues before running DQ analysis" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "[OK] Oracle connection test passed" -ForegroundColor Green

# Run DQ Analysis
Write-Host ""
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "Running Data Quality Analysis..." -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""

python DQ_Analysis_code\data_quality_analysis.py `
    --use-database `
    --config-file DQ_Analysis_code\oracle_connection_config.json `
    --generate-dashboard

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[ERROR] DQ analysis failed" -ForegroundColor Red
    Write-Host "Check the log file for details: dq_output_oracle_test\dq_oracle_run.log" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "============================================================================" -ForegroundColor Green
Write-Host "DQ Analysis Complete!" -ForegroundColor Green
Write-Host "============================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Output directory: dq_output_oracle_test" -ForegroundColor Cyan
Write-Host ""
Write-Host "Key files:" -ForegroundColor Cyan
Write-Host "  - dq_executive_dashboard.html  (Open in browser)" -ForegroundColor White
Write-Host "  - dq_executive_summary.txt     (Quick summary)" -ForegroundColor White
Write-Host "  - dq_summary.csv               (Detailed metrics)" -ForegroundColor White
Write-Host "  - good_records.csv             (Clean data)" -ForegroundColor White
Write-Host "  - dq_all_bad_records.csv       (Issues found)" -ForegroundColor White
Write-Host "  - dq_oracle_run.log            (Execution log)" -ForegroundColor White
Write-Host ""
Write-Host "============================================================================" -ForegroundColor Green

# Open dashboard in browser
if (Test-Path "dq_output_oracle_test\dq_executive_dashboard.html") {
    Write-Host ""
    Write-Host "Opening dashboard in browser..." -ForegroundColor Cyan
    Start-Process "dq_output_oracle_test\dq_executive_dashboard.html"
}

Read-Host "Press Enter to exit"

# Made with Bob
