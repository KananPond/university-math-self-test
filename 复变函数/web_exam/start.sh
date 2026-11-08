#!/usr/bin/env bash
# ==========================================================================
# 文件名：start.sh
# 作者：ZCode（GLM）
# 日期：2026-11-08
# 版本：1.0
# 文件说明：
# 1. 一键启动复变函数考试模拟系统（本地抽题与判分服务）。
# 2. 用法： ./start.sh [端口] [--no-open]
# 3. WSL2 下会自动调用 Windows 浏览器打开考试页面。
# ==========================================================================

set -euo pipefail

cd "$(dirname "$(readlink -f "$0")")"

PORT="8767"
NO_OPEN="0"

for arg in "$@"; do
    case "$arg" in
        --no-open)
            NO_OPEN="1"
            ;;
        ''|*[!0-9]*)
            echo "无法识别的参数：$arg"
            echo "用法： ./start.sh [端口] [--no-open]"
            exit 1
            ;;
        *)
            PORT="$arg"
            ;;
    esac
done

URL="http://127.0.0.1:${PORT}/"

# --------------------------------------------------------------------------
# 打开浏览器：依次尝试 WSL、Linux、macOS 下可用的方式
# --------------------------------------------------------------------------
open_browser()
{
    if [ "$NO_OPEN" = "1" ]; then
        return 0
    fi

    if command -v wslview >/dev/null 2>&1; then
        wslview "$URL" >/dev/null 2>&1 && return 0
    fi
    if command -v cmd.exe >/dev/null 2>&1; then
        cmd.exe /c start "" "$URL" >/dev/null 2>&1 && return 0
    fi
    if command -v explorer.exe >/dev/null 2>&1; then
        explorer.exe "$URL" >/dev/null 2>&1 && return 0
    fi
    if command -v xdg-open >/dev/null 2>&1; then
        xdg-open "$URL" >/dev/null 2>&1 && return 0
    fi
    if command -v open >/dev/null 2>&1; then
        open "$URL" >/dev/null 2>&1 && return 0
    fi

    echo "（未能自动打开浏览器，请手动访问上面的地址）"

    return 0
}

# --------------------------------------------------------------------------
# 端口占用检查
# --------------------------------------------------------------------------
port_in_use()
{
    if command -v ss >/dev/null 2>&1; then
        ss -ltn 2>/dev/null | grep -q ":${PORT}[[:space:]]" && return 0
    elif command -v netstat >/dev/null 2>&1; then
        netstat -ltn 2>/dev/null | grep -q ":${PORT}[[:space:]]" && return 0
    fi

    return 1
}

echo "=============================================="
echo " 复变函数考试模拟系统"
echo " 满分 100 分 · 限时 120 分钟"
echo "=============================================="
echo ""

if ! command -v python3 >/dev/null 2>&1; then
    echo "错误：未找到 python3，请先安装 Python 3。" >&2
    exit 1
fi

if port_in_use; then
    echo "端口 ${PORT} 已被占用，可能服务已经在运行。"
    echo "考试地址： ${URL}"
    echo ""
    open_browser
    exit 0
fi

echo "考试地址： ${URL}"
echo "闪电训练： ${URL}drill.html"
echo "复平面实验台： ${URL}plane.html"
echo "停止服务： 在本窗口按 Ctrl + C"
echo ""

echo "正在启动本地判分服务……"
echo ""

# 等服务起来再打开浏览器，避免出现空白页
if [ "$NO_OPEN" != "1" ]; then
    (
        sleep 2
        open_browser
    ) &
fi

exec python3 server.py "$PORT"
