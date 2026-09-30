# -*- coding: utf-8 -*-
"""抓完整报错"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from ed_product import EDProduct

pid = sys.argv[1]
p = EDProduct()
p.connect()
p.eval(f"location.href = 'https://ed.weeeg.com/ekadmin/product/add_product/{pid}'")
p.sleep(5)
p.eval("""(() => {
    window.__full = '';
    const O = XMLHttpRequest.prototype.open, S = XMLHttpRequest.prototype.send;
    XMLHttpRequest.prototype.open = function(m, u) { this.__u = u; return O.apply(this, arguments); };
    XMLHttpRequest.prototype.send = function(body) {
        const self = this;
        this.addEventListener('load', function() {
            if((self.__u||'').includes('product_goods')) window.__full = self.responseText || '';
        });
        return S.apply(this, arguments);
    };
    return 'OK';
})()""")
p.eval("""(() => {
    let priceInput = null;
    document.querySelectorAll('input').forEach(i => {
        const label = i.closest('.el-form-item')?.querySelector('label')?.textContent?.trim() || '';
        if(label.includes('售价')) priceInput = i;
    });
    let el = priceInput;
    for(let d = 0; d < 6 && el; d++) {
        if(el.__vue__ && el.__vue__.$options.name === 'ElInputNumber') { el.__vue__.setCurrentValue(1000); return 'SET'; }
        el = el.parentElement;
    }
})()""")
p.sleep(1)
p.eval("""(() => { const b = [...document.querySelectorAll('button')].find(x => x.textContent.trim() === '保存' && x.offsetParent !== null); b.click(); })()""")
p.sleep(5)
full = p.eval("window.__full")
d = json.loads(full)
# 只留关键信息
data = d.get("data", {})
print("msg:", d.get("msg"))
print("message:", data.get("message"))
tr = data.get("trace", [])
for t in tr[:5]:
    print("trace:", t.get("file","").split("/")[-1], t.get("line"), t.get("function","") or t.get("funct",""))
p.close()
