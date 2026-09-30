# 橱窗清退预警巡检

找出微信小店带货助手橱窗中的清退预警、不可售卖和非推广中商品，保留官方提示，输出 MD 报告与 JSON 明细。

## 安装与使用

```bash
git clone https://github.com/DaJunn/wechat-window-qingtui-scan.git ~/.agents/skills/wechat-window-qingtui-scan
cd ~/.agents/skills/wechat-window-qingtui-scan
python3 scripts/window_qingtui_scan.py
```

也可对 AI 说：「检查橱窗风险商品，列出官方原因和处理建议。」运行前需 Python 3、已连接扩展的 kimi-webbridge，以及已登录带货助手的 Chrome。

## 输出与边界

默认输出 `~/window_qingtui_check.md` 和 `~/window_qingtui_check.json`，再次运行会覆盖，需提前检查或调整脚本输出路径。

只读，不隐藏或移除商品。当前脚本最多采集 400 条，且请求异常可能导致漏页；须与后台总数和商品 ID 核对，未核对完整时只报告已读取范围。库存为零不单独计为本技能的风险。

完整流程、分类与故障处理见 [SKILL.md](SKILL.md)。更多技能见 [DaJunn](https://github.com/DaJunn)。
