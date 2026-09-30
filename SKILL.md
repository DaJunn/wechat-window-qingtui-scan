---
name: wechat-window-qingtui-scan
description: 微信小店带货助手橱窗「清退预警 + 不可售卖」快速巡检。扫描 store.weixin.qq.com/talent/channel/window 橱窗全量商品，找出带红色「清退预警」「不可售卖」标识及「结束推广」等非推广中状态的商品和官方提示文案，5-8秒出结论，输出 MD 报告 + JSON 全量数据。当用户说「清退预警」「橱窗清退预警」「跑下橱窗清退预警」「哪些商品要被清退」「不可售卖」「卖不了的商品」「橱窗风险商品」「橱窗预警巡检」「橱窗有没有预警商品」时使用。只读巡检，不代用户做移除/隐藏等写操作。
---

# 橱窗清退预警巡检

## 快速开始

确认前置条件后直接跑脚本：

```bash
python3 ~/.agents/skills/wechat-window-qingtui-scan/scripts/window_qingtui_scan.py
```

前置条件：
- kimi-webbridge daemon 运行中（`~/.kimi-webbridge/bin/kimi-webbridge status` 返回 `running:true` 且 `extension_connected:true`）
- Chrome 已登录 store.weixin.qq.com（带货助手账号）

脚本自动完成：直达 SSR 内容 frame → 读 localStorage 缓存的 magic 签名 → 全量重放 `getTalentWindowProducts` 接口（pageSize=20 翻页到底）→ 扫描每条商品的 `productRemindTips` 字段。签名失效时自动点一次「下一页」重抓再重放，无需人工干预。

## 输出与汇报

脚本落盘两个文件并向用户汇报：

- `~/window_qingtui_check.md` — 巡检报告
- `~/window_qingtui_check.json` — 全量商品数据（id/标题/店铺/价格/佣金/库存/预警状态）

汇报格式：结论先行（共 N 个商品、M 个风险：清退预警 X 个、不可售卖 Y 个），风险商品用表格列**标识/商品/店铺/售价/佣金/库存/官方提示原文**，再给动作建议：清退预警→联系商家换品、无改善则移除（原因是「销售质量」不是佣金）；不可售卖/结束推广→直接移除换新品，避免占橱窗位和拖累质量分。

## 风险标识识别口径

三类风险都算命中，按优先级打 `warnType` 标签：

1. `productRemindTips.remindStatusWording`（页面红色标识 rgba(250,81,81,1)）：「清退预警」「不可售卖」等，提示原文在 `remindDesc`；无标识商品该字段为空对象 `{}`
2. `statusWording` ≠「推广中」（如「结束推广」）
3. `itemCapability.canUse = false`（兜底判不可售卖）

```json
{
  "remindTitle": "不可售卖",
  "remindDesc": "商家已结束该商品的推广计划，该商品无法售卖。",
  "remindStatusWording": "不可售卖"
}
```

判断「无风险」前先校验 `total` 与页面「商品管理(N)」数字一致，防止漏页误报。注意：佣金字段可能为 `null`，报告生成已做容错；0 库存巡检属另一个 skill（wechat-store-window-stock），本 skill 不按库存判风险。

## 故障排查

- daemon 未就绪 → 按 kimi-webbridge skill 的 operations 流程先修复，不要绕过
- 输出「magic 缓存失效」后仍失败 → Chrome 未登录或登录态过期，请用户登录后重跑
- 反复找不到「下一页」按钮 → SSR 页没加载完，等 3 秒重跑一次；仍失败截图看页面是否弹了验证
- 接口重放返回 403「mcn magic invalid」→ 签名缓存损坏，清 localStorage 的 `wk_window_magic` 键后重跑（脚本会自动重抓）

## 边界

- 全程只读：不隐藏、不移除、不改价、不改库存
- 不把 magic 签名写进任何文件（只在浏览器 localStorage 里流转）
- 推送飞书/定时任务只在用户明确要求时做，不在本 skill 默认动作里
