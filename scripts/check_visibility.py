# -*- coding: utf-8 -*-
"""
check_visibility.py - 闲鱼商品搜索可见性诊断（买家视角自检，纯读取零风控）
原理：用 Chrome CDP 9222 新开 goofish.com 搜索页，滚动加载前 3 页结果，
     比对自家商品 ID 是否出现、出现在第几名，据此判断限流状态。

用法：
    python check_visibility.py "关键词" --ids 1077487223816,1079912988993
    python check_visibility.py "无人机航拍" --ids-file my_ids.txt   # 每行一个ID

判定规则（输出结论）：
    前 20 名能找到       -> ✅ 权重正常
    21-60 名             -> ⚠️ 权重偏低（标题/类目可优化）
    60 名后仍找不到      -> 🚫 强限流信号（再用 ID 直搜复核）
    关键词搜不到但 ID 直搜能到 -> 🚫 确认搜索降权

注意：登录态下搜索结果有轻微个性化，但「能不能搜到」这个硬指标不受影响。
"""

import json
import sys
import time

import requests

from cdp_tools import EDClient

CDP_URL = "http://127.0.0.1:9222"
MAX_RESULTS = 60  # 大约前 3 页


def open_search_tab(keyword):
    """在 9222 的 Chrome 里新开一个闲鱼搜索标签页"""
    url = f"https://www.goofish.com/search?q={requests.utils.quote(keyword)}"
    try:
        r = requests.put(f"{CDP_URL}/json/new?{url}", timeout=8)
    except Exception:
        r = requests.get(f"{CDP_URL}/json/new?{url}", timeout=8)
    tab = r.json()
    return tab


def extract_items(cli):
    """提取当前已加载的商品卡片：[{rank, item_id, title, price}]"""
    res = cli.eval(r"""(() => {
        const links = [...document.querySelectorAll('a[href*="/item?id="]')];
        const seen = new Set();
        const out = [];
        for (const a of links) {
            const m = a.href.match(/[?&]id=(\d+)/);
            if (!m || seen.has(m[1])) continue;
            seen.add(m[1]);
            const txt = (a.innerText || '').replace(/\s+/g, ' ').trim();
            const pm = txt.match(/¥\s*([\d.]+)/);
            out.push({id: m[1], text: txt.substring(0, 60), price: pm ? pm[1] : ''});
        }
        return JSON.stringify(out);
    })()""")
    try:
        return json.loads(res)
    except Exception:
        return []


def scroll_to_load(cli, target=MAX_RESULTS, max_scrolls=12):
    """滚动加载更多结果，直到数量达标或滚到底"""
    last = 0
    for i in range(max_scrolls):
        items = extract_items(cli)
        if len(items) >= target:
            return items[:target]
        if len(items) == last and i > 2:
            break  # 到底了
        last = len(items)
        cli.eval("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(2.5)
    return extract_items(cli)[:target]


def diagnose(keyword, my_ids):
    print(f"=== 闲鱼搜索可见性诊断 ===")
    print(f"关键词: {keyword}")
    print(f"待查商品 ID: {', '.join(my_ids) if my_ids else '(未提供，仅看搜索结果)'}")

    tab = open_search_tab(keyword)
    print(f"已打开搜索页: {tab.get('url', '')[:80]}")
    time.sleep(6)  # 等首屏加载

    cli = EDClient()
    cli.connect(url_pattern="goofish.com/search")

    # 等商品卡片渲染出来（最多 20 秒）
    cli.wait_for_selector('a[href*="/item?id="]', timeout=20)
    time.sleep(2)

    # 检查是否被登录墙/验证码挡住
    page_txt = cli.get_page_text(500)
    if "没有找到你想要的宝贝" in page_txt:
        print("⚠️ 该关键词官方结果为空（页面提示「没有找到你想要的宝贝」），下方展示的是猜你喜欢")
    elif "登录" in page_txt[:100] and "搜索" not in page_txt:
        print("⚠️ 页面疑似要求登录，搜索仍以游客态进行（反而更接近真实买家视角）")

    items = scroll_to_load(cli)
    print(f"\n共加载 {len(items)} 个搜索结果\n")

    for idx, it in enumerate(items, 1):
        mark = " 👈 我的" if it["id"] in my_ids else ""
        print(f"{idx:3d}. [{it['id']}] ¥{it['price']} {it['text'][:40]}{mark}")

    print("\n=== 诊断结论 ===")
    if not my_ids:
        print("未提供自家商品 ID，以上为纯搜索结果浏览。用 --ids 传入 ID 可做限流判定。")
    else:
        for mid in my_ids:
            hit = next((i for i, it in enumerate(items, 1) if it["id"] == mid), None)
            if hit is None:
                print(f"🚫 商品 {mid}: 前 {len(items)} 名未找到 -> 强限流信号")
                print(f"   复核方法：直接搜商品 ID {mid}，能搜到 = 确认搜索降权")
            elif hit <= 20:
                print(f"✅ 商品 {mid}: 第 {hit} 名 -> 权重正常")
            else:
                print(f"⚠️ 商品 {mid}: 第 {hit} 名 -> 权重偏低，可优化标题/类目")

    cli.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    keyword = sys.argv[1]
    ids = []
    if "--ids" in sys.argv:
        i = sys.argv.index("--ids")
        ids = [x.strip() for x in sys.argv[i + 1].split(",") if x.strip()]
    elif "--ids-file" in sys.argv:
        i = sys.argv.index("--ids-file")
        with open(sys.argv[i + 1], encoding="utf-8") as f:
            ids = [ln.strip() for ln in f if ln.strip()]
    diagnose(keyword, ids)
