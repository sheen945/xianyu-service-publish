# -*- coding: utf-8 -*-
"""对单个宝贝试不同价格，找保存成功的边界"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from ed_product import EDProduct

pid = sys.argv[1]
prices = sys.argv[2:]
p = EDProduct()
p.connect()
p.eval(f"location.href = 'https://ed.weeeg.com/ekadmin/product/add_product/{pid}'")
p.sleep(5)
p.eval("""(() => {
    window.__log = [];
    const O = XMLHttpRequest.prototype.open, S = XMLHttpRequest.prototype.send;
    XMLHttpRequest.prototype.open = function(m, u) { this.__u = u; return O.apply(this, arguments); };
    XMLHttpRequest.prototype.send = function(body) {
        const self = this;
        this.addEventListener('load', function() {
            if((self.__u||'').includes('product_goods')) {
                let pr = '';
                try { pr = JSON.parse(body).price; } catch(e) {}
                window.__log.push({price: pr, resp: (self.responseText||'').slice(0,120)});
            }
        });
        return S.apply(this, arguments);
    };
    return 'HOOKED';
})()""")
for price in prices:
    p.eval(f"""(() => {{
        let priceInput = null;
        document.querySelectorAll('input').forEach(i => {{
            const label = i.closest('.el-form-item')?.querySelector('label')?.textContent?.trim() || '';
            if(label.includes('售价')) priceInput = i;
        }});
        let el = priceInput;
        for(let d = 0; d < 6 && el; d++) {{
            if(el.__vue__ && el.__vue__.$options.name === 'ElInputNumber') {{ el.__vue__.setCurrentValue({price}); return 'SET'; }}
            el = el.parentElement;
        }}
        return 'NO';
    }})()""")
    p.sleep(1.2)
    p.eval("""(() => { const b = [...document.querySelectorAll('button')].find(x => x.textContent.trim() === '保存' && x.offsetParent !== null); b.click(); return 'OK'; })()""")
    p.sleep(4)
    log = json.loads(p.eval("JSON.stringify(window.__log)"))
    last = log[-1] if log else {}
    print(f"尝试 {price} -> 请求价:{last.get('price')} 响应:{last.get('resp','无')}")
p.close()
