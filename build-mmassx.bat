@echo off
setlocal enabledelayedexpansion

:: Dynamically determine source path (the folder where this script is located)
set SCRIPT_DIR=%~dp0
set SOURCE_DIR=%SCRIPT_DIR:~0,-1%
set BUILD_DIR=C:\build\mMassX
set ENV_DIR=%BUILD_DIR%\.mmass_env

echo [INFO] Locating conda.bat...
for /f "delims=" %%i in ('where conda.bat 2^>nul') do set "CONDA_BAT=%%i"

if not defined CONDA_BAT (
    echo [ERROR] conda.bat not found in PATH.
    echo Please ensure Miniconda or Anaconda is installed and "conda" is available in your system PATH.
    pause
    exit /b 1
)
echo [INFO] Using Conda at: %CONDA_BAT%

echo [1/7] Removing old build folder...
if exist "%BUILD_DIR%" (
    rmdir /s /q "%BUILD_DIR%"
)
mkdir "%BUILD_DIR%"

echo [2/7] Copying project from %SOURCE_DIR% to %BUILD_DIR% (excluding .git and .mmass_env) ...
robocopy "%SOURCE_DIR%" "%BUILD_DIR%" /E /XO /XD .git .mmass_env datasets

echo [3/7] Creating Conda environment with Python 3.9.19...
call "%CONDA_BAT%" create -y --prefix "%ENV_DIR%" python=3.9.19

echo [4/7] Installing packages into environment...
call "%CONDA_BAT%" install -y --prefix "%ENV_DIR%" -c conda-forge ^
    wxwidgets=3.1.5 ^
    wxpython=4.1.1 ^
    numpy=1.20.3 ^
    pandas=1.3.4 ^
    pyinstaller=6.9.0

echo [5/7] Running PyInstaller build...
cd /d "%BUILD_DIR%"
call "%CONDA_BAT%" activate "%ENV_DIR%"
"%ENV_DIR%\python.exe" -m PyInstaller --clean mmassx.spec

echo [6/7] Verifying build output...
if not exist "%BUILD_DIR%\dist" (
    echo [ERROR] Build failed — no 'dist' directory found.
    pause
    exit /b 1
)

if not exist "%BUILD_DIR%\dist\*.exe" (
    echo [ERROR] Build failed — no .exe created.
    pause
    exit /b 1
)

echo [7/7] Copying .exe files to %SOURCE_DIR%\dist ...
robocopy "%BUILD_DIR%\dist" "%SOURCE_DIR%\dist" *.exe /NFL /NDL /NJH /NJS /NC /NS /NP

echo [OK] Build complete. Executable(s) copied to %SOURCE_DIR%\dist
pause
endlocal