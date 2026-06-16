@echo off
echo ========================================
echo 声呐图像底质分类系统 - 服务启动脚本
echo ========================================

echo.
echo [1/4] 启动基础设施服务 (PostgreSQL, MinIO, Redis)...
docker-compose up -d postgres minio redis

echo.
echo [2/4] 等待服务启动...
timeout /t 15 /nobreak

echo.
echo [3/4] 启动后端 FastAPI 服务...
cd backend
start "Sonar Backend" cmd /k "cd /d %cd% && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
cd ..

echo.
echo [4/4] 启动前端 Vue3 开发服务器...
cd frontend
start "Sonar Frontend" cmd /k "cd /d %cd% && npm run dev"
cd ..

echo.
echo ========================================
echo 所有服务已启动！
echo ========================================
echo.
echo 后端 API: http://localhost:8000
echo API 文档: http://localhost:8000/docs
echo 前端界面: http://localhost:5173
echo MinIO 控制台: http://localhost:9001 (用户名: minioadmin, 密码: minioadmin)
echo.
echo 按任意键退出...
pause >nul
