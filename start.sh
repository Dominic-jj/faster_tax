#!/usr/bin/env bash
set -e

echo "============================================"
echo "   发票图片自动识别转电子发票"
echo "============================================"
echo ""

cd "$(dirname "$0")"

# 检查 Python
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "[错误] 未找到 Python，请先安装 Python 3.10+"
    exit 1
fi

PYTHON="python3"
if ! command -v python3 &> /dev/null; then
    PYTHON="python"
fi

# 检查并安装依赖
echo "[1/3] 检查依赖..."
if ! $PYTHON -c "import streamlit" 2>/dev/null; then
    echo "正在安装依赖（首次运行，请耐心等待）..."
    $PYTHON -m pip install -r requirements.txt
    echo "依赖安装完成。"
else
    echo "依赖已就绪。"
fi

# 创建输出目录
mkdir -p output

# 启动 Streamlit
echo ""
echo "[2/3] 启动应用..."
echo "[3/3] 浏览器将自动打开 http://localhost:8501"
echo ""
echo "按 Ctrl+C 停止服务"
echo "============================================"

$PYTHON -m streamlit run app.py --server.port=8501
