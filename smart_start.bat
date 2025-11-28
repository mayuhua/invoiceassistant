@echo off
chcp 65001 > nul
title Klarna Invoice Assistant - Smart Start

echo ========================================
echo   Klarna Invoice Assistant - Smart Start
echo ========================================
echo.

echo [1/4] 正在清理端口占用...
taskkill /F /IM python.exe > nul 2>&1
taskkill /F /IM node.exe > nul 2>&1
timeout /t 2 > nul

echo [2/4] 正在启动后端服务器...
start /B python server.py

echo [3/4] 等待后端初始化...
timeout /t 5 > nul

echo [4/4] 正在启动前端开发服务器...
cd frontend
start /B npm run dev

echo.
echo ========================================
echo   启动完成！
echo ========================================
echo.

REM 读取动态端口配置
if exist "..\port_config.json" (
    echo ✅ 后端配置已加载:
    for /f "tokens=2 delims=:," %%i in ('findstr /C:"backend_port" ..\port_config.json') do (
        set backend_port=%%i
        set backend_port=!backend_port: =!
    )
    set backend_port=!backend_port:~0,-1!
    echo    - 后端端口: !backend_port!
    echo    - 后端地址: http://localhost:!backend_port!
) else (
    echo ⚠️  使用默认端口 8000
    echo    - 后端地址: http://localhost:8000
)

echo.
echo 🌐 前端地址: http://localhost:5173
echo.
echo 现在可以打开浏览器访问前端了！
echo 按任意键关闭此窗口...
pause > nul