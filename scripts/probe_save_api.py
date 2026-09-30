# -*- coding: utf-8 -*-
"""挂钩XHR，抓取保存接口的请求和响应"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from ed_product import EDProduct

pid = sys.argv[1]
p = EDProduct()
p.connect()
p.eval(f"location.href = 'https://ed.weeeg.com/ekadmin/product/add_product/{pid}'")
p.sleep(5)
# 装钩子
p.eval("""(() => {
    window.__xhrLog = [];
    const O = XMLHttpRequest.prototype.open, S = XMLHttpRequest.prototype.send;
    XMLHttpRequest.prototype.open = function(m, u) { this.__u = u; this.__m = m; return O.apply(this, arguments); };
    XMLHttpRequest.prototype.send = function(body) {
        const self = this;
        this.addEventListener('load', function() {
            if((self.__u||'').includes('product') || (self.__u||'').includes('save') || (self.__u||'').includes('edit')) {
                window.__xhrLog.push({m: self.__m, u: self.__u, req: (body||'').toString().slice(0,600), resp: (self.responseText||'').slice(0,400)});
            }
        });
        return S.apply(this, arguments);
    };
    return 'HOOKED';
})()""")
# 改价
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
    return 'NO_VUE';
})()""")
p.sleep(1)
p.eval("""(() => { const b = [...document.querySelectorAll('button')].find(x => x.textContent.trim() === '保存' && x.offsetParent !== null); b.click(); return 'OK'; })()""")
p.sleep(5)
log = p.eval("JSON.stringify(window.__xhrLog)")
for item in json.loads(log):
    print("==", item["m"], item["u"])
    print("REQ:", item["req"][:500])
    print("RESP:", item["resp"][:300])
p.close()
