# -*- coding: utf-8 -*-
"""找 Vue 实例和售价绑定路径"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from ed_product import EDProduct

pid = sys.argv[1]
p = EDProduct()
p.connect()
p.eval(f"location.href = 'https://ed.weeeg.com/ekadmin/product/add_product/{pid}'")
p.sleep(5)
r = p.eval("""(() => {
    // 从售价输入框往上找带 __vue__ 的元素
    let priceInput = null;
    document.querySelectorAll('input').forEach(i => {
        const label = i.closest('.el-form-item')?.querySelector('label')?.textContent?.trim() || '';
        if(label.includes('售价')) priceInput = i;
    });
    if(!priceInput) return 'NO_INPUT';
    const out = {chain: []};
    let el = priceInput;
    for(let d = 0; d < 12 && el; d++) {
        if(el.__vue__) {
            const vm = el.__vue__;
            const keys = Object.keys(vm.$data || {});
            const dataPeek = {};
            keys.forEach(k => {
                const v = vm.$data[k];
                if(typeof v === 'number' || typeof v === 'string') dataPeek[k] = v;
                else if(v && typeof v === 'object') dataPeek[k] = Array.isArray(v) ? 'array('+v.length+')' : 'object{'+Object.keys(v).slice(0,8).join(',')+'}';
            });
            out.chain.push({depth: d, comp: vm.$options.name || vm.$options._componentTag || 'anon', data: dataPeek});
        }
        el = el.parentElement;
    }
    return JSON.stringify(out);
})()""")
d = json.loads(r)
for c in d["chain"]:
    print(f"深度{c['depth']} 组件:{c['comp']}")
    print("  data:", json.dumps(c["data"], ensure_ascii=False)[:400])
p.close()
