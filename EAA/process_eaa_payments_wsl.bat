@echo off
REM Batch script to run EAA Payment Processor from MS Access via WSL
REM Author: Lil Claudy Flossy

REM Run the Python script in WSL
echo Processing EAA Payment Documents via WSL...
echo ==========================================
echo.
echo This will:
echo - Find DOCX files in PaymentFiles/EAA
echo - Convert them to CSV format
echo - Import data to the database
echo - Update client IDs
echo - Archive processed files
echo.
echo Starting process...
echo.

wsl -d Ubuntu -e bash -c "cd /home/corpj/projects/dolla-bucks && source venv/bin/activate && cd EAA && python process_eaa_payments.py"

REM Check if the command succeeded
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ==========================================
    echo Processing completed successfully!
    echo Check the logs folder for details.
    echo ==========================================
) else (
    echo.
    echo ==========================================
    echo Processing failed with error code %ERRORLEVEL%
    echo Check the logs folder for error details.
    echo ==========================================
)

REM Pause to see the output
echo.
echo Press any key to close this window...
pause > nul