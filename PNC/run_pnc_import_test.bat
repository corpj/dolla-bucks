@echo off
REM PNC Import Script Runner for MS Access - TEST MODE
REM Author: Lil Claudy Flossy
REM This batch file runs the PNC import script in test mode through WSL

echo Starting PNC Import Process (TEST MODE)...
echo.
echo Running in TEST MODE - No database changes will be made
echo.

REM Run the Python script through WSL in test mode
wsl bash -c "cd /home/corpj/projects/dolla-bucks && source venv/bin/activate && python PNC/import_pnc_payments.py --test"

REM Check if the command was successful
if %ERRORLEVEL% EQU 0 (
    echo.
    echo PNC Import test completed successfully!
    echo Check the logs in PNC/logs/ for details.
) else (
    echo.
    echo ERROR: PNC Import test failed with error code %ERRORLEVEL%
    echo Please check the logs in PNC/logs/ for details.
)

echo.
echo Press any key to close this window...
pause >nul