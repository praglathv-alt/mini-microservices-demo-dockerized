@echo off
echo Starting all microservices...
echo.

start "USER SERVICE (5002)" cmd /k python user_service.py
timeout /t 1 >nul

start "PRODUCT SERVICE (5001)" cmd /k python product_service.py
timeout /t 1 >nul

start "ORDER SERVICE (5003)" cmd /k python order_service.py
timeout /t 1 >nul

start "API GATEWAY (5000)" cmd /k python api_gateway.py
timeout /t 2 >nul

echo.
echo All 4 services launched in separate windows.
echo Open your browser and go to: http://127.0.0.1:5000
echo.
start http://127.0.0.1:5000
pause
