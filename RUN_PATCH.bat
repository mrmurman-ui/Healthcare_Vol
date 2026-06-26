@echo off
echo ============================================
echo  Citizens Patch — CA Codes + National IDs
echo ============================================
cd /d "%~dp0"
echo.
echo Step 1: Checking psycopg2...
py -3.12 -c "import psycopg2; print('psycopg2 OK')" 2>nul || (
    echo Installing psycopg2...
    py -3.12 -m pip install psycopg2-binary --quiet
)
echo.
echo Step 2: Running patch...
py -3.12 scripts\patch_citizens_now.py
echo.
echo Step 3: Done! Restart Streamlit now.
pause
