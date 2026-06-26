@echo off
echo ============================================
echo  Applying Citizens Page Fix
echo ============================================

set TARGET=C:\Users\pOr Bannikul\AppData\Local\Python\pythoncore-3.14-64\Healthcare_Production_02

REM 1. Copy new files
echo Copying files...
copy /Y "%~dp0app\modules\citizens\page.py" "%TARGET%\app\modules\citizens\page.py"
copy /Y "%~dp0app\modules\citizens\profile.py" "%TARGET%\app\modules\citizens\profile.py"

REM 2. Delete pycache so Python uses new files
echo Clearing pycache...
if exist "%TARGET%\app\modules\citizens\__pycache__" (
    rmdir /s /q "%TARGET%\app\modules\citizens\__pycache__"
    echo Cleared citizens pycache
)

echo.
echo DONE. Now restart Streamlit.
echo ============================================
pause
