@echo off
rem ==========================================================================
rem 文件名：start.bat
rem 作者：ZCode（GLM）
rem 日期：2026-10-02
rem 版本：1.0
rem 文件说明：
rem 1. Windows 下双击即可启动线性代数考试模拟系统。
rem 2. 本系统只需要 Python（无需 gcc），直接用本机 Python 启动。
rem 3. 用法： 双击，或在命令行执行 start.bat [端口]
rem ==========================================================================

chcp 65001 >nul
setlocal
set "PYTHONUTF8=1"

set "PORT=%~1"
if "%PORT%"=="" set "PORT=8766"

echo ==============================================
echo  线性代数考试模拟系统
echo  正在启动本地判分服务……
echo ==============================================
echo.

set "PY="
where python >nul 2>&1
if not errorlevel 1 set "PY=python"
if not defined PY (
    where py >nul 2>&1
    if not errorlevel 1 set "PY=py -3"
)

if not defined PY (
    echo 错误：未找到 Python，请先安装 Python 3.8 及以上版本。
    echo 安装后重新运行本脚本即可。
    echo.
    pause
    exit /b 1
)

rem 延迟 2 秒后自动打开浏览器（等服务就绪）
start "" cmd /c "timeout /t 2 /nobreak >nul & start "" http://127.0.0.1:%PORT%/"

%PY% "%~dp0server.py" %PORT%

echo.
echo 服务已停止。
pause
