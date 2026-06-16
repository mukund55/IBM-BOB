# Ab Initio Code Analyzer Web Application Startup Script
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Ab Initio Code Analyzer Web Application" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Flask is installed
try {
    python -c "import flask" 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Flask not installed"
    }
} catch {
    Write-Host "Flask is not installed. Installing dependencies..." -ForegroundColor Yellow
    pip install -r requirements_web.txt
    Write-Host ""
}

Write-Host "Starting web server..." -ForegroundColor Green
Write-Host ""
Write-Host "Open your browser and navigate to:" -ForegroundColor Yellow
Write-Host "http://localhost:5000" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

python web_analyzer_app.py

# Made with Bob
