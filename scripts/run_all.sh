#!/bin/bash
# AI Agent 学习项目 - 运行所有实验（演示模式）
# 需要从项目根目录执行:  cd AI-Agent-Learning-Project && bash scripts/run_all.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$SCRIPT_DIR"

echo "============================================"
echo "  AI Agent 学习项目 - 实验运行"
echo "============================================"

# 实验 1
echo ""
echo "--- 实验 1: 基础工具调用助手 ---"
cd experiments/exp01-weather-assistant
python main.py eval
cd "$SCRIPT_DIR"

# 实验 2
if [ -f "experiments/exp02-doc-qa-eval/sample_doc/sample.txt" ]; then
    echo ""
    echo "--- 实验 2: 单文档问答 + 评估 ---"
    cd experiments/exp02-doc-qa-eval
    python main.py batch
    cd "$SCRIPT_DIR"
fi

# 实验 3
echo ""
echo "--- 实验 3: 自动化工单处理 ---"
cd experiments/exp03-ticket-processor
python main.py
cd "$SCRIPT_DIR"

# 实验 4
echo ""
echo "--- 实验 4: 多 Agent 客服对比 ---"
cd experiments/exp04-multi-agent
python compare.py 2>/dev/null || echo "  ⚠ 实验 4 需要 OPENAI_API_KEY 环境变量"
cd "$SCRIPT_DIR"

# 实验 5
echo ""
echo "--- 实验 5: 质量监控与退化检测 ---"
cd experiments/exp05-quality-monitor
python main.py
cd "$SCRIPT_DIR"

echo ""
echo "============================================"
echo "  所有实验运行完成"
echo "============================================"
