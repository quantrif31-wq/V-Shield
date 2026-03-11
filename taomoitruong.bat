@echo off
title Setup V-Shield Environment

echo =============================
echo BAT DAU TAO MOI TRUONG
echo =============================

:: ROOT PATH
set ROOT=C:\DoAnTotNghiep\V-Shield\AI_Project
set APIROOT=C:\DoAnTotNghiep\V-Shield\API\API\API
set VIEWROOT=C:\DoAnTotNghiep\V-Shield\View

:: -----------------------------
:: DOC_BIEN
:: -----------------------------
echo.
echo Dang tao moi truong cho DOC_BIEN...

cd /d %ROOT%\doc_bien

python -m venv venv
if %errorlevel% neq 0 (
    echo Loi khi tao venv trong doc_bien
    pause
    exit /b
)

call venv\Scripts\activate

pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Loi khi cai requirements doc_bien
    pause
    exit /b
)

echo DOC_BIEN CAI DAT THANH CONG
echo.

:: -----------------------------
:: FACE_RECOGNITION
:: -----------------------------
echo Dang tao moi truong cho FACE_RECOGNITION...

cd /d %ROOT%\face_recognition

python -m venv venv
if %errorlevel% neq 0 (
    echo Loi khi tao venv trong face_recognition
    pause
    exit /b
)

call venv\Scripts\activate

pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Loi khi cai requirements face_recognition
    pause
    exit /b
)

echo FACE_RECOGNITION CAI DAT THANH CONG
echo.

:: -----------------------------
:: RESET DATABASE ASP.NET CORE
:: -----------------------------
echo Dang reset database ASP.NET Core...

cd /d %APIROOT%

echo Xoa database...
dotnet ef database drop -f

echo Xoa thu muc Migrations...
rmdir /s /q Migrations

echo Tao lai migration...
dotnet ef migrations add InitialCreate

echo Cap nhat database...
dotnet ef database update

if %errorlevel% neq 0 (
    echo Loi khi tao database ASP.NET
    pause
    exit /b
)

echo DATABASE ASP.NET TAO THANH CONG
echo.

:: -----------------------------
:: VUE INSTALL
:: -----------------------------
echo Dang cai dat package Vue...

cd /d %VIEWROOT%

npm install

if %errorlevel% neq 0 (
    echo Loi khi cai npm package
    pause
    exit /b
)

echo VUE PACKAGE CAI DAT THANH CONG
echo.

echo =============================
echo TOAN BO MOI TRUONG DA SAN SANG
echo =============================

pause