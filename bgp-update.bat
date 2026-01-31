@echo off
chcp 65001 >nul
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0bgp-update.ps1"
set /p lastver=<"bgp_lastversion_2.txt"
timeout /t 0 /nobreak >nul
if "%1" == "-nolog" goto nolog
if "%lastver%" == "1.0" (
    echo.
    echo      BGP update     
    echo Обновления не найдены.
    echo.
) else (
    del bgp_lastversion_2.txt
    del bgp_lastversion.txt
    echo.
    echo Обновление найдено!
    echo.
    goto update
)
del bgp_lastversion_2.txt
del bgp_lastversion.txt
exit /b 0
:nolog
if "%lastver%" == "1.0" (
    echo no
) else (
    echo yes
)
del bgp_lastversion_2.txt
del bgp_lastversion.txt
exit /b 0
:update
set URL=http://localhost/bgp-vs.php?ver=%lastver%
for /f "delims=" %%a in ('curl -s "%URL%"') do (
    set "response=%%a"
)
echo Server response: %response%
echo Validating response...
if "%response%" == "unknown version" (
    echo Response is invalid!
    exit /b 1
) else (
    echo Response is valid!
)
echo Downloading installer...
set URL=http://localhost/bgp-vi.php?ver=%lastver%
for /f "delims=" %%a in ('curl -s "%URL%"') do (
    set "response2=%%a"
)
echo Downloading paused
echo Loading installer args...
echo Server response: %response2%
echo Validating response...
if "%response2%" == "unknown version" (
    echo Response is invalid!
    exit /b 1
) else (
    echo Response is valid!
)
echo Downloading installer...
powershell -NoLogo -NoProfile -Command Invoke-WebRequest -Uri "%response%" -OutFile "setup-%lastver%-x64-Windows11.exe"
echo Checking for installer...
if exist "setup-%lastver%-x64-Windows11.exe" (
    echo Installer find: setup-%lastver%-x64-Windows11.exe
) else (
    echo Installer not found!
    exit /b 9
)
echo Running installer...
echo The installer will request to run as administrator. You will need to perform an action in another window.
call setup-%lastver%-x64-Windows11.exe %response2%
echo Ended!