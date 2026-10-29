rem                                                         .\run_tests.bat
```bat
@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul

cd /d "%~dp0"

:menu
cls
echo ==============================
echo       EVSim - Test Runner
echo ==============================
echo.

set /a count=0

for /r testing_sandbox %%F in (*.py) do (
    if not "%%~nxF"=="__init__.py" (
        set /a count+=1
        set "file[!count!]=%%~nF"
        set "path[!count!]=%%~dpF"
        set "fullpath[!count!]=%%~fF"
        echo !count!. %%~nF
    )
)

if !count! EQU 0 (
    echo Тесты не найдены.
    pause
    exit /b
)

echo.
echo 0. Выход
echo.

set "choice="
set /p "choice=Выбери тест: "

if "!choice!"=="0" exit /b

if not defined file[!choice!] (
    echo.
    echo Неверный выбор.
    pause
    goto menu
)

:run_test
set "selected="

for %%F in ("!fullpath[%choice%]!") do (
    set "selected=%%~dpnF"
)

set "selected=!selected:%CD%\=!"

for /f "tokens=*" %%M in ('powershell -NoProfile -Command "'!selected!'.Replace('\','.')"') do set "selected=%%M"

echo.
echo Запуск: !file[%choice%]!
echo ==============================
C:\Users\user\Desktop\python\python.exe -m !selected!

echo.
echo ==============================
echo Тест завершён.
echo.
echo 1. Повторить текущий тест
echo 2. Запустить другой тест
echo 0. Завершить тестирование
echo.

choice /c 120 /n /m "Твой выбор: "

if errorlevel 3 exit /b
if errorlevel 2 goto menu
if errorlevel 1 goto run_test
