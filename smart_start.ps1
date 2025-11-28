# Klarna Invoice Assistant - Smart Start Script
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Klarna Invoice Assistant - Smart Start" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/4] 清理端口占用..." -ForegroundColor Yellow
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
Get-Process node -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2

Write-Host "[2/4] 启动后端服务器..." -ForegroundColor Yellow
$backendJob = Start-Job -ScriptBlock { python server.py }

Write-Host "[3/4] 等待后端初始化..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

Write-Host "[4/4] 启动前端开发服务器..." -ForegroundColor Yellow
Set-Location frontend
$frontendJob = Start-Job -ScriptBlock { npm run dev }

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  启动完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# 读取端口配置
if (Test-Path "../port_config.json") {
    Write-Host "✅ 后端配置已加载:" -ForegroundColor Green
    $config = Get-Content "../port_config.json" | ConvertFrom-Json
    Write-Host "   - 后端端口: $($config.backend_port)" -ForegroundColor White
    Write-Host "   - 后端地址: http://localhost:$($config.backend_port)" -ForegroundColor White
} else {
    Write-Host "⚠️  使用默认端口 8000" -ForegroundColor Yellow
    Write-Host "   - 后端地址: http://localhost:8000" -ForegroundColor White
}

Write-Host ""
Write-Host "🌐 前端地址: http://localhost:5173" -ForegroundColor White
Write-Host ""
Write-Host "现在可以打开浏览器访问前端了！" -ForegroundColor Cyan
Write-Host "按 Ctrl+C 停止所有服务" -ForegroundColor Yellow

# 保持脚本运行
try {
    while ($true) {
        Start-Sleep -Seconds 1
    }
}
finally {
    Write-Host "正在停止所有服务..." -ForegroundColor Yellow
    Stop-Job $backendJob -ErrorAction SilentlyContinue
    Stop-Job $frontendJob -ErrorAction SilentlyContinue
    Remove-Job $backendJob -ErrorAction SilentlyContinue
    Remove-Job $frontendJob -ErrorAction SilentlyContinue
    Write-Host "所有服务已停止。" -ForegroundColor Green
}