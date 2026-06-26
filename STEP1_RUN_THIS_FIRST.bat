@echo off
echo Copying citizens pages...
SET SRC=%~dp0
SET DST=%~dp0..\..\

REM Try common paths
SET P1=C:\Users\pOr Bannikul\AppData\Local\Python\pythoncore-3.14-64\Healthcare_Production_02
SET P2=C:\Users\pOr Bannikul\Desktop\Healthcare_Production_02
SET P3=C:\Healthcare_Production_02

FOR %%P IN ("%P1%" "%P2%" "%P3%") DO (
    IF EXIST "%%~P\app\modules\citizens" (
        echo Found at: %%~P
        copy /Y "%SRC%app\modules\citizens\page.py"    "%%~P\app\modules\citizens\page.py"
        copy /Y "%SRC%app\modules\citizens\profile.py" "%%~P\app\modules\citizens\profile.py"
        copy /Y "%SRC%scripts\patch_citizens_now.py"   "%%~P\scripts\patch_citizens_now.py"
        IF EXIST "%%~P\app\modules\citizens\__pycache__" (
            rmdir /s /q "%%~P\app\modules\citizens\__pycache__"
            echo Cleared pycache
        )
        echo Files copied successfully!
        echo.
        echo Now run in Healthcare_Production_02 folder:
        echo   py -3.12 scripts\patch_citizens_now.py
        echo Then restart Streamlit.
        GOTO :EOF
    )
)
echo Could not find Healthcare_Production_02 folder automatically.
echo Please copy files manually.
pause
