# -*- coding: utf-8 -*-
"""深挖售价区：规格表/Vue数据"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from ed_product import EDProduct

pid = sys.argv[1]
p = EDProduct()
p.connect()
p.eval(f"location.href = 'https://ed.weeeg.com/ekadmin/product/add_product/{pid}'")
p.sleep(5)
r = p.eval("""(() => {
    const out = {tables: [], specArea: '', vue: null};
    // 规格区所有表格
    document.querySelectorAll('.el-table').forEach((t, i) => {
        const heads = [...t.querySelectorAll('th')].map(h => h.textContent.trim());
        const rows = [];
        t.querySelectorAll('.el-table__body-wrapper tbody tr').forEach(tr => {
            rows.push([...tr.querySelectorAll('td')].map(td => {
                const inp = td.querySelector('input');
                return inp ? ('INPUT:' + inp.value) : td.textContent.trim().slice(0,20);
            }));
        });
        out.tables.push({i, heads, rows: rows.slice(0,3)});
    });
    // 找 Vue 实例数据
    const app = document.querySelector('#app');
    if(app && app.__vue__) {
        try {
            const f = (vm, depth) => {
                if(depth > 4 || !vm) return null;
                if(vm.form && typeof vm.form === 'object') {
                    const keys = Object.keys(vm.form);
                    if(keys.some(k => /price|money|amount/i.test(k))) {
                        const sub = {};
                        keys.forEach(k => { if(/price|money|amount|spec|sku/i.test(k)) sub[k] = JSON.stringify(vm.form[k]).slice(0,300); });
                        return sub;
                    }
                }
                return f(vm.$children && vm.$children[0], depth+1);
            };
            out.vue = f(app.__vue__, 0);
        } catch(e) { out.vue = 'ERR:' + e.message; }
    }
    return JSON.stringify(out);
})()""")
d = json.loads(r)
print("-- 表格 --")
for t in d["tables"]:
    print(f"表{t['i']} 表头:{t['heads']}")
    for row in t["rows"]: print("   ", row)
print("-- VUE 表单价格相关 --")
print(json.dumps(d["vue"], ensure_ascii=False, indent=1) if d["vue"] else "未找到")
p.close()
