# -*- coding: utf-8 -*-
"""探查易店「编辑商品」界面结构（只读，不保存）"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from ed_product import EDProduct

p = EDProduct()
p.connect()
p.open_product_page()
p.sleep(2)

# 搜索 编队表演
p.eval("""(() => {
    const inputs = document.querySelectorAll('input.el-input__inner, input[placeholder]');
    for(const i of inputs){
        const ph = i.placeholder || '';
        if(ph.includes('搜索') || ph.includes('商品') || ph.includes('宝贝') || ph.includes('标题')){
            i.value = '编队表演';
            i.dispatchEvent(new Event('input', {bubbles:true}));
            i.dispatchEvent(new Event('change', {bubbles:true}));
            return 'TYPED:' + ph;
        }
    }
    return 'NO_INPUT';
})()""")
p.sleep(1)
p.eval("""(() => {
    const btns = document.querySelectorAll('button');
    for(const b of btns){ if(b.textContent.trim().includes('搜索')){ b.click(); return 'CLICKED_SEARCH'; } }
    const inputs = document.querySelectorAll('input.el-input__inner');
    for(const i of inputs){ if(i.value){ i.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true})); return 'ENTER'; } }
    return 'NO_BTN';
})()""")
p.sleep(3)

# 读行
rows = p.read_current_page_rows()
print("ROWS:", json.dumps(rows, ensure_ascii=False)[:800])

# 点第一行的 更多 -> 编辑商品
r = p.row_more(0, "编辑商品")
print("MORE:", r)
p.sleep(3)

# 看页面变成什么了：URL + 可见 dialog / 新页面标题
info = p.eval("""(() => {
    const out = {url: location.href, title: document.title, dialogs: [], tabs: []};
    document.querySelectorAll('.el-dialog').forEach(d => {
        const st = getComputedStyle(d);
        if(st.display !== 'none' && d.offsetParent !== null){
            out.dialogs.push((d.querySelector('.el-dialog__title')||{}).textContent || 'dialog');
        }
    });
    document.querySelectorAll('.el-tabs__item').forEach(t => out.tabs.push(t.textContent.trim()));
    return JSON.stringify(out);
})()""")
print("PAGE:", info)
p.close()
