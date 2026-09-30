# -*- coding: utf-8 -*-
"""闲鱼后台出售列表探查：找表演宝贝和改价入口"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, r"C:\Users\Administrator\.workbuddy\skills\xianyu-service-publish\scripts")
from cdp_tools import CDP

c = CDP()
c.connect_tab("goofish.com/sell")
c.sleep(3)
r = c.eval("""(() => {
    const out = {title: document.title, login: !document.body.innerText.includes('登录'), items: []};
    // 出售中列表条目
    document.querySelectorAll('[class*="item"], [class*="card"], tr').forEach(el => {
        const t = (el.innerText||'').trim();
        if(t.includes('表演') && t.length < 300) {
            const btns = [...el.querySelectorAll('button, a, span')].map(b => b.textContent.trim()).filter(x => x && x.length < 8);
            out.items.push({text: t.slice(0,120), btns: [...new Set(btns)].slice(0,12)});
        }
    });
    out.items = out.items.slice(0, 8);
    return JSON.stringify(out);
})()""")
d = json.loads(r)
print("页面:", d["title"], "| 已登录:", d["login"])
for it in d["items"]:
    print("--", it["text"][:80].replace("\n"," / "))
    print("   按钮:", it["btns"])
c.close()
