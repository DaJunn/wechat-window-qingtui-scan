#!/usr/bin/env python3
"""
橱窗「清退预警」快速巡检 — WaveKOL
用法: python3 ~/wavekol/09_自动化脚本/window_qingtui_scan.py
依赖: kimi-webbridge daemon (127.0.0.1:10086) + Chrome 已登录 store.weixin.qq.com

速度设计:
  1. 直接打开内容 frame 的 SSR 地址 /talent/ssr/channel/window/（普通 light DOM，工具全能直接操作）
  2. magic 签名头缓存在 localStorage，命中就直接重放接口，不再点 UI
  3. 缓存失效(403)才点一次「下一页」重新抓签名，然后重放
输出: ~/window_qingtui_check.md + ~/window_qingtui_check.json
"""
import json
import os
import sys
import time
import urllib.request

DAEMON = "http://127.0.0.1:10086/command"
SESSION = "window-qingtui-scan"
SSR_URL = "https://store.weixin.qq.com/talent/ssr/channel/window/"
API_URL = "https://store.weixin.qq.com/shop-faas/mmeckolwindownode/window/getTalentWindowProducts?token=&lang=zh_CN"
OUT_MD = os.path.expanduser("~/window_qingtui_check.md")
OUT_JSON = os.path.expanduser("~/window_qingtui_check.json")


def cmd(action, args=None, retries=2, timeout=90):
    payload = json.dumps({"action": action, "args": args or {}, "session": SESSION})
    last = None
    for i in range(retries + 1):
        try:
            req = urllib.request.Request(
                DAEMON, data=payload.encode(), headers={"Content-Type": "application/json"}
            )
            return json.loads(urllib.request.urlopen(req, timeout=timeout).read().decode())
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(1.5)
    raise RuntimeError(f"daemon {action} failed: {last}")


def ev(code, timeout=90):
    r = cmd("evaluate", {"code": code}, timeout=timeout)
    if not r.get("ok"):
        raise RuntimeError(f"evaluate failed: {r}")
    return r["data"]["value"] if isinstance(r.get("data"), dict) else r["data"]


# ---------- JS 片段 ----------

JS_REPLAY_ALL = r"""
(async () => {
  const API = '__API__';
  const cached = JSON.parse(localStorage.getItem('wk_window_magic') || 'null');
  const go = (H, offset) => new Promise(res => {
    const x = new XMLHttpRequest();
    x.open('POST', API);
    x.setRequestHeader('Content-Type', 'application/json');
    x.setRequestHeader('biz_magic', H.biz_magic);
    x.setRequestHeader('talent_magic', H.talent_magic);
    x.setRequestHeader('potter-scene', H.potter_scene || '');
    x.timeout = 15000;
    x.onload = () => { try { res(((JSON.parse(x.responseText).data || {}).products) || []); } catch(e) { res([]); } };
    x.onerror = () => res([]);
    x.ontimeout = () => res([]);
    x.send(JSON.stringify({pageSize:20, offset:offset, productSource:null, reqSource:1}));
  });
  let all = [];
  if (cached && cached.biz_magic && cached.talent_magic) {
    const first = await go(cached, 0);
    if (first.length) {
      all = first;
      for (let off = 20; off < 400; off += 20) {
        const p = await go(cached, off);
        all.push(...p);
        if (p.length < 20) break;
      }
    }
  }
  if (!all.length) return JSON.stringify({needMagic: true});
  const flagged = [];
  const statuses = {};
  const warnTypes = {};
  const list = [];
  for (const p of all) {
    statuses[p.statusWording] = (statuses[p.statusWording] || 0) + 1;
    const tip = (p.productRemindTips && Object.keys(p.productRemindTips).length) ? p.productRemindTips : null;
    const canUse = !p.itemCapability || p.itemCapability.canUse !== false;
    // 风险标识：清退预警 / 不可售卖（tips）> 结束推广等非推广中状态 > canUse=false
    let warnType = '';
    if (tip && tip.remindStatusWording) warnType = tip.remindStatusWording;
    else if (p.statusWording && p.statusWording !== '推广中') warnType = p.statusWording;
    else if (!canUse) warnType = '不可售卖';
    if (warnType) {
      warnTypes[warnType] = (warnTypes[warnType] || 0) + 1;
      flagged.push({
        productId: p.productId, title: p.title, shortTitle: p.shortTitle,
        shop: p.platformName, price: p.minPrice / 100,
        commissionRate: p.commissionInfo.commissionRate / 10000,
        commissionEstimate: p.commissionInfo.commissionEstimate / 100,
        stock: p.stock, status: p.statusWording, warnType: warnType, tips: tip,
        spuId: p.outProductId
      });
    }
    list.push({id: p.productId, title: (p.title || '').slice(0, 60), shop: p.platformName,
               price: p.minPrice / 100, rate: p.commissionInfo.commissionRate / 10000,
               stock: p.stock, status: p.statusWording, warn: warnType});
  }
  return JSON.stringify({needMagic: false, total: all.length, statuses: statuses, warnTypes: warnTypes, flagged: flagged, list: list});
})()
""".replace("__API__", API_URL)

JS_ARM_CAPTURE = r"""
(() => {
  if (window.__wkCap) { window.__hdrs = {}; return 'rearmed'; }
  window.__wkCap = true; window.__hdrs = {};
  const oo = XMLHttpRequest.prototype.open, os = XMLHttpRequest.prototype.send, osr = XMLHttpRequest.prototype.setRequestHeader;
  XMLHttpRequest.prototype.open = function(m, u) { this.__u = String(u); return oo.apply(this, arguments); };
  XMLHttpRequest.prototype.setRequestHeader = function(k, v) {
    if (this.__u && this.__u.includes('getTalentWindowProducts')) window.__hdrs[k] = v;
    return osr.call(this, k, v);
  };
  return 'armed';
})()
"""

JS_READ_MAGIC = r"""
(() => {
  const H = window.__hdrs || {};
  if (H.biz_magic && H.talent_magic) {
    localStorage.setItem('wk_window_magic', JSON.stringify({biz_magic: H.biz_magic, talent_magic: H.talent_magic, potter_scene: H['potter-scene'] || '', t: Date.now()}));
    return 'saved';
  }
  return 'no_headers';
})()
"""


def capture_magic_via_ui():
    """点一次「下一页」让应用自己发请求，截下 magic 签名头存入 localStorage"""
    cmd("evaluate", {"code": JS_ARM_CAPTURE})
    # 找「下一页」ref（SSR frame 里 ref 很少，快照很小）
    d = cmd("snapshot", {})
    refs = []

    def walk(nodes):
        for n in nodes:
            if n.get("ref"):
                refs.append((n.get("name", "").strip(), n["ref"]))
            walk(n.get("children", []))

    walk(d.get("data", {}).get("tree", []))
    nxt = [r for n, r in refs if "下一页" in n]
    if not nxt:
        raise RuntimeError("找不到「下一页」按钮，页面可能未加载完")
    cmd("click", {"selector": nxt[0]})
    time.sleep(2.5)
    return ev(JS_READ_MAGIC)


def fmt_num(v, spec):
    """价格/佣金字段可能为 null，容错格式化"""
    return format(v, spec) if isinstance(v, (int, float)) else "-"


def write_report(data):
    flagged = data["flagged"]
    total = data["total"]
    statuses = data["statuses"]
    status_line = "、".join(f"{k} {v}个" for k, v in statuses.items())
    lines = []
    lines.append("# 微信小店带货助手 · 橱窗「清退预警」巡检")
    lines.append("")
    lines.append("- 页面：https://store.weixin.qq.com/talent/channel/window")
    lines.append(f"- 巡检时间：{time.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"- 口径：橱窗列表接口 `getTalentWindowProducts` 全量分页，共 {total} 个商品（{status_line}）")
    lines.append("- 数据状态：真实数据（页面同源接口），非模拟")
    lines.append("")
    if not flagged:
        lines.append("## 结论")
        lines.append("")
        lines.append(f"全部 {total} 个商品均无「清退预警 / 不可售卖」等风险标识。")
    else:
        warn_line = "、".join(f"{k} {v}个" for k, v in data.get("warnTypes", {}).items())
        lines.append(f"## 结论：{len(flagged)} 个商品带风险标识（{warn_line}）")
        lines.append("")
        lines.append("| 标识 | 商品 | 店铺 | 售价 | 佣金率 | 库存 | 官方提示 |")
        lines.append("|---|---|---|---|---|---|---|")
        for f in flagged:
            desc = (f["tips"].get("remindDesc") if f["tips"] else "") or ""
            desc = desc.replace("|", "，")
            lines.append(
                f"| **{f['warnType']}** | {f['title']} | {f['shop']} | ¥{fmt_num(f['price'], '.2f')} | {fmt_num(f['commissionRate'], '.1f')}%（预估 ¥{fmt_num(f['commissionEstimate'], '.2f')}） | {f['stock'] if f['stock'] is not None else '-'} | {desc} |"
            )
        lines.append("")
        for f in flagged:
            lines.append(f"- [{f['warnType']}] {f['title']} — 商品 ID：{f['productId']}（联盟 SPU：{f['spuId']}），状态：{f['status']}")
    lines.append("")
    lines.append("## 识别方式")
    lines.append("")
    lines.append("「清退预警 / 不可售卖」在列表接口商品字段 `productRemindTips.remindStatusWording`（红色 rgba(250,81,81,1)），无标识商品该字段为空对象；`statusWording` 非「推广中」（如「结束推广」）或 `itemCapability.canUse=false` 也计为风险商品。")
    lines.append("")
    lines.append(f"全量明细见 `window_qingtui_check.json`。")
    with open(OUT_MD, "w") as fp:
        fp.write("\n".join(lines) + "\n")
    with open(OUT_JSON, "w") as fp:
        json.dump({"total": total, "statuses": statuses, "flagged": flagged, "list": data["list"]}, fp, ensure_ascii=False, indent=1)


def main():
    t0 = time.time()
    # 0) daemon 健康检查
    st = json.loads(os.popen(os.path.expanduser("~/.kimi-webbridge/bin/kimi-webbridge status")).read() or "{}")
    if not (st.get("running") and st.get("extension_connected")):
        print("kimi-webbridge 未就绪，先启动 daemon 并连接 Chrome 扩展")
        sys.exit(1)

    # 1) 直达内容 frame
    cmd("navigate", {"url": SSR_URL})
    for _ in range(10):
        time.sleep(1.2)
        try:
            ready = ev("document.body ? document.body.innerText.length : 0")
            if isinstance(ready, (int, float)) and ready > 500:
                break
        except Exception:  # noqa: BLE001
            pass

    # 2) 用缓存签名直接全量重放
    r = json.loads(ev(JS_REPLAY_ALL, timeout=120))

    # 3) 缓存失效则点一次「下一页」重新抓签名再重放
    if r.get("needMagic"):
        print("magic 缓存失效，点「下一页」重新抓签名…")
        state = capture_magic_via_ui()
        if state != "saved":
            print("抓签名失败（应用没发请求），重试一次")
            capture_magic_via_ui()
        r = json.loads(ev(JS_REPLAY_ALL, timeout=120))
        if r.get("needMagic"):
            print("重放仍失败，请确认 Chrome 已登录 store.weixin.qq.com")
            sys.exit(1)

    write_report(r)
    flagged = r["flagged"]
    print(f"完成：{r['total']} 个商品，{len(flagged)} 个清退预警，耗时 {time.time()-t0:.1f}s")
    for f in flagged:
        print(f"  - {f['title']} | {f['shop']} | ¥{f['price']:.2f} | {f['tips'].get('remindDesc','')}")
    print(f"报告: {OUT_MD}\n数据: {OUT_JSON}")
    try:
        cmd("close_session")
    except Exception:  # noqa: BLE001
        pass


if __name__ == "__main__":
    main()
