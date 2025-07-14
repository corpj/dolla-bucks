@echo off
REM PNC Import Script Runner for MS Access
REM Author: Lil Claudy Flossy
REM This batch file runs the PNC import script through WSL

echo Starting PNC Import Process...
echo.

REM Run the Python script through WSL
REM The wsl command executes commands in the WSL environment
REM We navigate to the project directory and activate the virtual environment before running the script
wsl bash -c "cd /home/corpj/projects/dolla-bucks && source venv/bin/activate && python PNC/import_pnc_payments.py"

REM Check if the command was successful
if %ERRORLEVEL% EQU 0 (
    echo.
    echo PNC Import completed successfully!
    echo Check the logs in PNC/logs/ for details.
) else (
    echo.
    echo ERROR: PNC Import failed with error code %ERRORLEVEL%
    echo Please check the logs in PNC/logs/ for details.
)

echo.
echo Press any key to close this window...
pause >nul