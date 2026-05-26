# Data Quality Analysis Runner Script (PowerShell)
# This script runs the data quality analysis from the correct directory

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Data Quality Analysis Tool" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Change to the script directory
Set-Location $PSScriptRoot

Write-Host "Current Directory: $(Get-Location)" -ForegroundColor Yellow
Write-Host ""

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.7 or higher" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""

# Check if required packages are installed
Write-Host "Checking required packages..." -ForegroundColor Yellow
try {
    python -c "import pandas, numpy" 2>&1 | Out-Null
    Write-Host "Required packages found!" -ForegroundColor Green
} catch {
    Write-Host "WARNING: Required packages not found" -ForegroundColor Yellow
    Write-Host "Installing pandas, numpy, and openpyxl..." -ForegroundColor Yellow
    pip install pandas numpy openpyxl
}

Write-Host ""
Write-Host "Running Data Quality Analysis..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Run the analysis with sample data
python data_quality_analysis.py --input-file sample_customer_data.csv

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Analysis Complete!" -ForegroundColor Green
Write-Host "Check the dq_output folder for results" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Read-Host "Press Enter to exit"

# Made with Bob
