@echo off
echo ================================================
echo  Run this from Healthcare_Production_02 folder
echo ================================================
cd /d "%~dp0"
py -3.12 scripts\patch_and_verify.py
pause
