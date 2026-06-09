@echo off
title Build Family Safety Monitor

echo ============================================
echo   Family Safety Monitor - PyInstaller Build
echo ============================================
echo.

python --version > nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found.
    pause
    exit /b 1
)

echo [1/5] Pinning numpy ^< 2 to match torch ABI...
pip install "numpy<2" -q
if errorlevel 1 (
    echo [ERROR] numpy downgrade failed.
    pause
    exit /b 1
)

echo [2/5] Installing dependencies...
pip install pyinstaller pillow ultralytics opencv-python openai requests -q
if errorlevel 1 (
    echo [ERROR] pip install failed.
    pause
    exit /b 1
)

echo [3/5] Checking model file...
if not exist "yolov8n-face-lindevs.pt" (
    echo       [WARN] yolov8n-face-lindevs.pt not found. Will auto-download on first run.
) else (
    echo       OK
)

echo [4/5] Cleaning old build/dist...
if exist build rmdir /s /q build
if exist dist  rmdir /s /q dist

echo [5/5] Running PyInstaller...
pyinstaller --noconfirm --clean "家庭安全监控工具.spec"
if errorlevel 1 (
    echo.
    echo [ERROR] PyInstaller failed. Paste the last 20-30 error lines.
    pause
    exit /b 1
)

echo.
echo ============================================
echo   BUILD SUCCESS
echo   Output: dist\家庭安全监控工具.exe
echo ============================================
echo.

set /p open_dir="Open dist folder? (y/n): "
if /i "%open_dir%"=="y" explorer dist

pause
