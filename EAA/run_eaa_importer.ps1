# PowerShell script to run EAA DB Importer from MS Access
# Author: Lil Claudy Flossy

# Get the script directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectPath = Split-Path -Parent $scriptPath

# Change to project directory
Set-Location $projectPath

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Green
& ".\venv\Scripts\Activate.ps1"

# Change to EAA directory
Set-Location ".\EAA"

# Run the importer
Write-Host "`nRunning EAA Database Importer..." -ForegroundColor Yellow
python eaa_db_importer.py

# Check exit code
if ($LASTEXITCODE -eq 0) {
    Write-Host "`nImport completed successfully!" -ForegroundColor Green
    Write-Host "Check the logs folder for details." -ForegroundColor Cyan
} else {
    Write-Host "`nImport failed with error code $LASTEXITCODE" -ForegroundColor Red
    Write-Host "Check the logs folder for error details." -ForegroundColor Yellow
}

# Keep window open
Write-Host "`nPress any key to close this window..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")