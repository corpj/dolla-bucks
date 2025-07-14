@echo off
REM Wells Fargo Import Script Runner for MS Access - Latest File Only
REM Author: Lil Claudy Flossy
REM This batch file runs the WF Excel import script for the latest file only

echo Starting Wells Fargo Import Process (Latest File)...
echo.

REM Run the Python script through WSL - default behavior processes latest file
wsl bash -c "cd /home/corpj/projects/dolla-bucks && source venv/bin/activate && python WF/wf_excel_importer.py"

REM Check if the command was successful
if %ERRORLEVEL% EQU 0 (
    echo.
    echo Wells Fargo Import completed successfully!
    echo Check the logs in WF/ directory for details.
) else (
    echo.
    echo ERROR: Wells Fargo Import failed with error code %ERRORLEVEL%
    echo Please check the logs in WF/ directory for details.
)

echo.
echo Press any key to close this window...
pause >nul