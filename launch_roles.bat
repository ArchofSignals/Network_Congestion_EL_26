@echo off
setlocal

set "PORT=8501"
set "BASE_URL=http://localhost:%PORT%"

cd /d "%~dp0"

echo Starting Network Congestion Simulator on %BASE_URL% ...
start "Network Congestion Streamlit Server" cmd /k python -m streamlit run main.py --server.port %PORT%

echo Waiting for Streamlit to start...
timeout /t 5 /nobreak >nul

echo Opening role pages...
start "" "%BASE_URL%/?role=sender"
start "" "%BASE_URL%/?role=admin"
start "" "%BASE_URL%/?role=receiver"

echo.
echo Opened:
echo   Sender:   %BASE_URL%/?role=sender
echo   Admin:    %BASE_URL%/?role=admin
echo   Receiver: %BASE_URL%/?role=receiver
echo.
echo Close the Streamlit server window when you are done.

endlocal
