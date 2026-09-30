# -*- coding: utf-8 -*-
"""修正售价：先探查价格区结构，再精准修改并保存"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from ed_product import EDProduct

IDS = ["1077854738546","1074550698790","1073613999098","1073988642744","1028157586875","1070773126255"]

p = EDProduct()
p.connect()

# 先探查第一个的价格区结构
pid = IDS[0]
p.eval(f"location.href = 'https://ed.weeeg.com/ekadmin/product/add_product/{pid}'")
p.sleep(4)
probe = p.eval("""(() => {
    const out = [];
    document.querySelectorAll('input').forEach((i, idx) => {
        if(i.type==='hidden' || i.offsetParent===null) return;
        const label = i.closest('.el-form-item')?.querySelector('label')?.textContent?.trim() || '';
        const td = i.closest('td');
        const th = td ? td.closest('table')?.querySelectorAll('th')[[...td.parentNode.children].indexOf(td)]?.textContent?.trim() : '';
        if(label.includes('售价') || label.includes('价格') || label.includes('规格') || (th||'').includes('价')) {
            out.push({idx, label, th, val: i.value, tag: i.outerHTML.slice(0,120)});
        }
    });
    return JSON.stringify(out);
})()""")
print("价格区结构:", json.dumps(json.loads(probe), ensure_ascii=False, indent=1))
p.close()
