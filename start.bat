@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

if not exist "output" mkdir output

echo ============================================
echo    Invoice OCR to Excel
echo ============================================
echo.
echo Starting...
echo.

python -m streamlit run app.py --server.port=8501
pause
