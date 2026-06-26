# 实验 5：Agent 质量监控与退化检测系统

## 实验目标

建立 Agent 质量监控体系，自动发现退化。

## 实验内容

1. 收集 Agent 对话日志
2. 自动化评估 pipeline
3. 退化检测与告警
4. 离线回放回归测试

## 运行方式

```bash
pip install openai rich
python main.py          # 启动监控
python main.py eval     # 运行评估 pipeline
python main.py replay   # 离线回放
```
