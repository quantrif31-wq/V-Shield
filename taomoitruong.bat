@echo off
title Setup V-Shield Environment
color 0A

echo =========================================
echo        SETUP HE THONG V-SHIELD
echo =========================================
echo.

:: ==============================
:: PATH CONFIG
:: ==============================
set ROOT=C:\DoAnTotNghiep\V-Shield\AI_Project
set APIROOT=C:\DoAnTotNghiep\V-Shield\API\API\API
set VIEWROOT=C:\DoAnTotNghiep\V-Shield\View

:: ==============================
:: KIEM TRA PHAN MEM
:: ==============================

echo Kiem tra Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
echo ❌ Python chua duoc cai!
pause
goto end
)

echo Kiem tra NodeJS...
node -v >nul 2>&1
if %errorlevel% neq 0 (
echo ❌ NodeJS chua duoc cai!
pause
goto end
)

echo Kiem tra .NET SDK...
dotnet --version >nul 2>&1
if %errorlevel% neq 0 (
echo ❌ .NET SDK chua duoc cai!
pause
goto end
)

echo ✔ Tat ca cong cu da san sang
echo.

:: =====================================================
:: DOC_BIEN
:: =====================================================

echo =========================================
echo TAO MOI TRUONG DOC_BIEN
echo =========================================

cd /d %ROOT%\doc_bien

python -m venv venv
if %errorlevel% neq 0 (
echo ❌ Loi tao venv DOC_BIEN
pause
goto end
)

call venv\Scripts\activate

pip install -r requirements.txt
if %errorlevel% neq 0 (
echo ❌ Loi pip install DOC_BIEN
pause
goto end
)

echo ✔ DOC_BIEN OK
echo.

:: =====================================================
:: FACE_RECOGNITION
:: =====================================================

echo =========================================
echo TAO MOI TRUONG FACE_RECOGNITION
echo =========================================

cd /d %ROOT%\face_recognition

python -m venv venv
if %errorlevel% neq 0 (
echo ❌ Loi tao venv FACE_RECOGNITION
pause
goto end
)

call venv\Scripts\activate

pip install -r requirements.txt
if %errorlevel% neq 0 (
echo ❌ Loi pip install FACE_RECOGNITION
pause
goto end
)

echo ✔ FACE_RECOGNITION OK
echo.

:: =====================================================
:: ASP.NET CORE DATABASE
:: =====================================================

echo =========================================
echo RESET DATABASE ASP.NET
echo =========================================

cd /d %APIROOT%

echo Restore NuGet...
dotnet restore
if %errorlevel% neq 0 (
echo ❌ Loi dotnet restore
pause
goto end
)

echo Build project...
dotnet build
if %errorlevel% neq 0 (
echo ❌ Loi build project
pause
goto end
)

echo Drop database...
dotnet ef database drop -f

echo Delete migrations...
if exist Migrations (
rmdir /s /q Migrations
)

echo Create migration...
dotnet ef migrations add InitialCreate
if %errorlevel% neq 0 (
echo ❌ Loi tao migration
pause
goto end
)

echo Update database...
dotnet ef database update
if %errorlevel% neq 0 (
echo ❌ Loi update database
pause
goto end
)

echo ✔ DATABASE OK
echo.

:: =====================================================
:: VUE INSTALL
:: =====================================================

echo =========================================
echo CAI DAT VUE PACKAGE
echo =========================================

cd /d %VIEWROOT%

echo Dang chay npm install...
echo.

cmd /k "npm install"

if %errorlevel% neq 0 (
    echo.
    echo =====================================
    echo LOI KHI CAI DAT NPM PACKAGE
    echo KIEM TRA NODEJS HOAC PACKAGE.JSON
    echo =====================================
    pause
    goto end
)

echo.
echo ✔ VUE PACKAGE CAI DAT THANH CONG
echo.
:: =====================================================
:: HOAN THANH
:: =====================================================

echo =========================================
echo   TAT CA MOI TRUONG DA CAI DAT THANH CONG
echo =========================================
echo.

:end
echo.
echo Nhan phim bat ky de thoat...
pause >nul