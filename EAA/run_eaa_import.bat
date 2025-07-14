@echo off
REM EAA Import Script Runner for MS Access
REM Author: Lil Claudy Flossy
REM This batch file runs the EAA process and import script through WSL

echo Starting EAA Import Process...
echo.
echo This will process the latest Word document in PaymentFiles/EAA/
echo.

REM Get the latest .docx file from the EAA directory
REM Note: User should place the Word document in PaymentFiles/EAA/ before running
wsl bash -c "cd /home/corpj/projects/dolla-bucks && source venv/bin/activate && latest_file=$(ls -t PaymentFiles/EAA/*.docx 2>/dev/null | head -1); if [ -z \"$latest_file\" ]; then echo 'ERROR: No Word documents found in PaymentFiles/EAA/'; exit 1; else echo \"Processing file: $latest_file\"; python EAA/process_and_import.py \"$latest_file\"; fi"

REM Check if the command was successful
if %ERRORLEVEL% EQU 0 (
    echo.
    echo EAA Import completed successfully!
    echo Check the logs in EAA/ directory for details.
) else (
    echo.
    echo ERROR: EAA Import failed with error code %ERRORLEVEL%
    echo Please check:
    echo 1. Word documents exist in PaymentFiles/EAA/
    echo 2. The logs in EAA/ directory for details
)

echo.
echo Press any key to close this window...
pause >nul