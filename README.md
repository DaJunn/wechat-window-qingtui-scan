# wechat-window-qingtui-scan

**橱窗清退预警巡检** —— 5-8 秒找出清退预警、不可售卖、非推广中的商品

让 AI agent（DSH / Codex / Claude Code 等）使用。

## 解决什么问题

之前商品被平台标记清退预警 / 不可售卖，往往等到卖不动了才发现。

现在 5-8 秒扫完橱窗，找出带「清退预警」「不可售卖」标识及「结束推广」等非推广中状态的商品和官方提示文案，输出 MD 报告 + JSON 全量数据。

## 前置依赖

1. **kimi-webbridge daemon** 在跑：
   ```bash
   ~/.kimi-webbridge/bin/kimi-webbridge status   # 要 running:true + extension_connected:true
   ```
   没装：`curl -fsSL https://cdn.kimi.com/webbridge/install.sh | bash`
2. **Chrome 已登录** `store.weixin.qq.com`（微信小店带货助手）。本系列只复用你自己已打开的标签页，**不代登录**。

## 安装

```bash
git clone https://github.com/DaJunn/wechat-window-qingtui-scan.git \
  ~/.agents/skills/wechat-window-qingtui-scan
```

## 触发方式

对 agent 说：「清退预警」「跑下橱窗清退预警」「哪些商品要被清退」「不可售卖」「橱窗有没有预警商品」。


## 说明

- **只读巡检**，不代用户做移除 / 隐藏等写操作

## 相关

- 完整技能合集见飞书文档《AI减负视频号运营技能合集》
- 更多 skill：https://github.com/DaJunn
