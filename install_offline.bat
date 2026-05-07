@echo off
setlocal
cd /d "%~dp0"

echo [PXN-Reader] Creating virtual environment with the current computer's Python...
py -m venv .venv
if errorlevel 1 goto error

echo [PXN-Reader] Installing dependencies from offline_wheels without internet access...
.venv\Scripts\python.exe -m pip install --no-index --find-links=offline_wheels -r requirements.txt
if errorlevel 1 goto error

echo.
echo [PXN-Reader] Offline installation completed successfully.
echo You can now double-click start_pxn_reader.bat to start the Streamlit app.
pause
exit /b 0

:error
echo.
echo [PXN-Reader] Offline installation failed. Please check that Python is installed and offline_wheels exists.
pause
exit /b 1
