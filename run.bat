@echo off
title Run V-Shield System

echo =============================
echo Starting V-Shield System
echo =============================

:: RUN ASP.NET CORE API
echo Starting ASP.NET Core API...
start cmd /k "cd /d C:\DoAnTotNghiep\V-Shield\API\API\API && dotnet run --launch-profile "https"

:: RUN VUE FRONTEND
echo Starting Vue Frontend...
start cmd /k "cd /d C:\DoAnTotNghiep\V-Shield\View && npm run dev"

echo.
echo =============================
echo All services started
echo =============================

pause