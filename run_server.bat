@echo off
title RO 순수 점검일지 시스템 (사내 & 외부 공개 서버)
echo ========================================================
echo   RO 순수 점검일지 시스템을 시작합니다.
echo   - 사내 Wi-Fi 접속 주소: http://192.168.0.13:8000
echo ========================================================
echo.

cd /d "%~dp0"
start "FastAPI_Server" "C:\Users\sall0\AppData\Roaming\Python\Python314\Scripts\uvicorn.exe" main:app --host 0.0.0.0 --port 8000
timeout /t 3 > nul

echo.
echo ========================================================
echo LTE/5G 모바일 전용 외부 인터넷 주소를 생성 중입니다...
echo ========================================================
echo.
npx -y localtunnel --port 8000
pause
