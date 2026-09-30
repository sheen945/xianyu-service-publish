# -*- coding: utf-8 -*-
"""通过 ElInputNumber 组件方法 setCurrentValue 改价，保存并回读"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from ed_product import EDProduct

IDS = sys.argv[1:]
p = EDProduct()
p.connect()
for pid in IDS:
    p.eval(f"location.href = 'https://ed.weeeg.com/ekadmin/product/add_product/{pid}'")
    p.sleep(5)
    r = p.eval("""(() => {
        let priceInput = null;
        document.querySelectorAll('input').forEach(i => {
            const label = i.closest('.el-form-item')?.querySelector('label')?.textContent?.trim() || '';
            if(label.includes('售价')) priceInput = i;
        });
        if(!priceInput) return 'NO_INPUT';
        let el = priceInput;
        for(let d = 0; d < 6 && el; d++) {
            if(el.__vue__ && el.__vue__.$options.name === 'ElInputNumber') {
                const vm = el.__vue__;
                if(typeof vm.setCurrentValue === 'function') { vm.setCurrentValue(1000); }
                else { vm.currentValue = 1000; vm.$emit('input', 1000); vm.$emit('change', 1000); }
                return 'SET_OK currentValue=' + vm.currentValue;
            }
            el = el.parentElement;
        }
        return 'NO_VUE';
    })()""")
    p.sleep(1.5)
    s = p.eval("""(() => {
        const b = [...document.querySelectorAll('button')].find(x => x.textContent.trim() === '保存' && x.offsetParent !== null);
        if(!b) return 'NO_SAVE'; b.click(); return 'SAVED';
    })()""")
    p.sleep(4)
    msg = p.eval("""(() => { const m = document.querySelector('.el-message'); return m ? m.textContent.trim().slice(0,40) : 'NO_MSG'; })()""")
    # 回读
    p.eval(f"location.href = 'https://ed.weeeg.com/ekadmin/product/add_product/{pid}'")
    p.sleep(5)
    v = p.eval("""(() => {
        let val = '';
        document.querySelectorAll('input').forEach(i => {
            const label = i.closest('.el-form-item')?.querySelector('label')?.textContent?.trim() || '';
            if(label.includes('售价')) val = i.value;
        });
        return val;
    })()""")
    print(pid, "|", r, "| 提示:", msg, "| 回读:", v)
p.close()
