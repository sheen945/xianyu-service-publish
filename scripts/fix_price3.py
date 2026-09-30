# -*- coding: utf-8 -*-
"""重试失败的 5 个：模拟真实键入改售价"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from ed_product import EDProduct

IDS = ["1077854738546","1074550698790","1073613999098","1073988642744","1070773126255"]

p = EDProduct()
p.connect()
for pid in IDS:
    p.eval(f"location.href = 'https://ed.weeeg.com/ekadmin/product/add_product/{pid}'")
    p.sleep(5)
    # 找到售价输入框坐标，真实点击聚焦
    coord = p.eval("""(() => {
        let found = null;
        document.querySelectorAll('input').forEach(i => {
            const label = i.closest('.el-form-item')?.querySelector('label')?.textContent?.trim() || '';
            if(label.includes('售价')) found = i;
        });
        if(!found) return 'NO_PRICE';
        found.scrollIntoView({block:'center'});
        const r = found.getBoundingClientRect();
        return JSON.stringify({x: Math.round(r.left + r.width/2), y: Math.round(r.top + r.height/2)});
    })()""")
    if 'NO_PRICE' in coord:
        print(pid, "没找到售价框"); continue
    c = json.loads(coord)
    p.sleep(1)
    p.mouse_click(c["x"], c["y"])
    p.sleep(0.8)
    # 全选删除再键入
    p.eval("""(() => {
        let found = null;
        document.querySelectorAll('input').forEach(i => {
            const label = i.closest('.el-form-item')?.querySelector('label')?.textContent?.trim() || '';
            if(label.includes('售价')) found = i;
        });
        found.focus();
        found.select();
        const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        setter.call(found, '');
        found.dispatchEvent(new Event('input', {bubbles:true}));
        setter.call(found, '1000');
        found.dispatchEvent(new Event('input', {bubbles:true}));
        found.dispatchEvent(new Event('change', {bubbles:true}));
        found.blur();
        return found.value;
    })()""")
    p.sleep(1.5)
    cur = p.eval("""(() => {
        let v='';
        document.querySelectorAll('input').forEach(i => {
            const label = i.closest('.el-form-item')?.querySelector('label')?.textContent?.trim() || '';
            if(label.includes('售价')) v = i.value;
        });
        return v;
    })()""")
    s = p.eval("""(() => {
        const b = [...document.querySelectorAll('button')].find(x => x.textContent.trim() === '保存' && x.offsetParent !== null);
        if(!b) return 'NO_SAVE'; b.click(); return 'SAVED';
    })()""")
    p.sleep(4)
    msg = p.eval("""(() => { const m = document.querySelector('.el-message'); return m ? m.textContent.trim().slice(0,40) : 'NO_MSG'; })()""")
    print(pid, "| 页面价:", cur, "| 提示:", msg)
p.close()
print("DONE")
