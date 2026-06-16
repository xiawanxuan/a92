@echo off
echo ========================================
echo 安装后端 Python 依赖...
echo ========================================

cd backend
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo.
echo ========================================
echo 依赖安装完成！
echo ========================================
pause
