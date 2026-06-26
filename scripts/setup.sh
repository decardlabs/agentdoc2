#!/bin/bash
# AI Agent 学习项目 - 环境设置脚本

set -e

echo "=== 环境设置 ==="

# 1. 检查 Python
PYTHON=$(command -v python3)
if [ -z "$PYTHON" ]; then
    echo "❌ 未找到 Python3"
    exit 1
fi
echo "✅ Python: $($PYTHON --version)"

# 2. 检查 API Key（DeepSeek）
if [ -z "$DEEPSEEK_API_KEY" ]; then
    echo "⚠ 未设置 DEEPSEEK_API_KEY"
    echo "  请申请并设置: export DEEPSEEK_API_KEY='sk-...'"
    echo "  申请地址: https://platform.deepseek.com/api_keys"
else
    echo "✅ DEEPSEEK_API_KEY 已设置"
fi

# 3. 创建虚拟环境
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    $PYTHON -m venv venv
    echo "✅ 虚拟环境已创建"
fi

echo "激活: source venv/bin/activate"

# 4. 安装全局依赖
echo "安装全局依赖..."
source venv/bin/activate
pip install -r requirements.txt --quiet
echo "✅ 全局依赖已安装"

echo ""
echo "=== 环境就绪 ==="
echo "开始学习: cd experiments/exp01-weather-assistant && python main.py"
