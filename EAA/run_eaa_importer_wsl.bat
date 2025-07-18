@echo off
REM Batch script to run EAA Payment Processor from MS Access via WSL
REM Author: Lil Claudy Flossy

REM Run the Python script in WSL
echo Running EAA Payment Processor via WSL...
wsl -d Ubuntu -e bash -c "cd /home/corpj/projects/dolla-bucks && source venv/bin/activate && cd EAA && python process_eaa_payments.py"

REM Check if the command succeeded
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