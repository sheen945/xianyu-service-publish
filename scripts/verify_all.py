# -*- coding: utf-8 -*-
"""回读 6 个宝贝最终 标题/价格/描述首行"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from ed_product import EDProduct

IDS = ["1077854738546","1074550698790","1073613999098","1073988642744","1028157586875","1070773126255"]
p = EDProduct()
p.connect()
for pid in IDS:
    p.eval(f"location.href = 'https://ed.weeeg.com/ekadmin/product/add_product/{pid}'")
    p.sleep(4)
    v = p.eval("""(() => {
        const out = {t:'',pr:'',d:''};
        document.querySelectorAll('input').forEach(i => {
            const label = i.closest('.el-form-item')?.querySelector('label')?.textContent?.trim() || '';
            if(label.includes('宝贝标题')) out.t = i.value;
            if(label.includes('售价')) out.pr = i.value;
        });
        document.querySelectorAll('textarea').forEach(t => {
            const label = t.closest('.el-form-item')?.querySelector('label')?.textContent?.trim() || '';
            if(label.includes('宝贝描述')) out.d = (t.value||'').split('\\n')[0];
        });
        return JSON.stringify(out);
    })()""")
    d = json.loads(v)
    ok = "OK" if d["pr"] == "1000.00" and "固定翼" in d["t"] else "!!"
    print(f"{ok} {pid} | 价:{d['pr']} | 题:{d['t'][:28]} | 述:{d['d'][:24]}")
p.close()
