# -*- coding: utf-8 -*-
"""读取指定宝贝编辑页的完整标题+描述（只读）"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from ed_product import EDProduct

pid = sys.argv[1]
p = EDProduct()
p.connect()
p.eval(f"location.href = 'https://ed.weeeg.com/ekadmin/product/add_product/{pid}'")
p.sleep(4)
info = p.eval("""(() => {
    const out = {title:'', desc:'', price:''};
    document.querySelectorAll('input').forEach(i => {
        const label = i.closest('.el-form-item')?.querySelector('label')?.textContent?.trim() || '';
        if(label.includes('宝贝标题')) out.title = i.value;
        if(label.includes('售价')) out.price = i.value;
    });
    document.querySelectorAll('textarea').forEach(t => {
        const label = t.closest('.el-form-item')?.querySelector('label')?.textContent?.trim() || '';
        if(label.includes('宝贝描述')) out.desc = t.value;
    });
    return JSON.stringify(out);
})()""")
import json
d = json.loads(info)
print("标题:", d["title"])
print("价格:", d["price"])
print("描述:")
print(d["desc"])
p.close()
