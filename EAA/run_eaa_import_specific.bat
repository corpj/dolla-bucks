@echo off
REM EAA Import Script Runner for MS Access - Specific File
REM Author: Lil Claudy Flossy
REM This batch file allows importing a specific file

echo Starting EAA Import Process...
echo.

REM Check if a file was passed as parameter
if "%~1"=="" (
    echo ERROR: No file specified!
    echo Usage: run_eaa_import_specific.bat "filename.docx"
    echo.
    echo Example: run_eaa_import_specific.bat "eaa_1234_01312025.docx"
    echo.
    pause
    exit /b 1
)

set FILENAME=%~1
echo Processing file: %FILENAME%
echo.

REM Run the Python script with the specific file
wsl bash -c "cd /home/corpj/projects/dolla-bucks && source venv/bin/activate && python EAA/process_and_import.py \"PaymentFiles/EAA/%FILENAME%\""

REM Check if the command was successful
if %ERRORLEVEL% EQU 0 (
    echo.
    echo EAA Import completed successfully!
    echo Check the logs in EAA/ directory for details.
) else (
    echo.
    echo ERROR: EAA Import failed with error code %ERRORLEVEL%
    echo Please check the logs in EAA/ directory for details.
)

echo.
echo Press any key to close this window...
pause >nul