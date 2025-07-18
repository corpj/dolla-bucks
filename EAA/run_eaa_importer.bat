@echo off
REM Batch script to run EAA DB Importer from MS Access
REM Author: Lil Claudy Flossy

REM Change to the project directory
cd /d "%~dp0\.."

REM Activate the virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Change to EAA directory
cd EAA

REM Run the importer script
echo Running EAA Database Importer...
python eaa_db_importer.py

REM Check if the script ran successfully
if %ERRORLEVEL% EQU 0 (
    echo.
    echo Import completed successfully!
    echo Check the logs folder for details.
) else (
    echo.
    echo Import failed with error code %ERRORLEVEL%
    echo Check the logs folder for error details.
)

REM Pause to see the output
echo.
echo Press any key to close this window...
pause > nul