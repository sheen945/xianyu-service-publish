# -*- coding: utf-8 -*-
"""修正 6 个宝贝售价 -> 1000（完整事件链），保存后回读验证"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from ed_product import EDProduct

IDS = ["1077854738546","1074550698790","1073613999098","1073988642744","1028157586875","1070773126255"]

p = EDProduct()
p.connect()
for pid in IDS:
    p.eval(f"location.href = 'https://ed.weeeg.com/ekadmin/product/add_product/{pid}'")
    p.sleep(4)
    r = p.eval("""(() => {
        const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        let found = null;
        document.querySelectorAll('input').forEach(i => {
            const label = i.closest('.el-form-item')?.querySelector('label')?.textContent?.trim() || '';
            if(label.includes('售价')) found = i;
        });
        if(!found) return 'NO_PRICE';
        setter.call(found, '1000');
        found.dispatchEvent(new Event('input', {bubbles:true}));
        found.dispatchEvent(new Event('change', {bubbles:true}));
        found.dispatchEvent(new Event('blur', {bubbles:true}));
        found.focus(); found.blur();
        return 'SET:' + found.value;
    })()""")
    p.sleep(1)
    s = p.eval("""(() => {
        const b = [...document.querySelectorAll('button')].find(x => x.textContent.trim() === '保存' && x.offsetParent !== null);
        if(!b) return 'NO_SAVE'; b.click(); return 'SAVED';
    })()""")
    p.sleep(3)
    msg = p.eval("""(() => { const m = document.querySelector('.el-message'); return m ? m.textContent.trim().slice(0,40) : 'NO_MSG'; })()""")
    # 回读验证
    p.eval(f"location.href = 'https://ed.weeeg.com/ekadmin/product/add_product/{pid}'")
    p.sleep(4)
    v = p.eval("""(() => {
        let val = '';
        document.querySelectorAll('input').forEach(i => {
            const label = i.closest('.el-form-item')?.querySelector('label')?.textContent?.trim() || '';
            if(label.includes('售价')) val = i.value;
        });
        return val;
    })()""")
    print(pid, "填写:", r, "| 保存:", s, "| 提示:", msg, "| 回读价:", v)
p.close()
print("DONE")
