# -*- coding: utf-8 -*-
"""探查编辑页字段结构（只读）"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from ed_product import EDProduct

p = EDProduct()
p.connect()
info = p.eval("""(() => {
    const out = {url: location.href, inputs: [], textareas: [], editors: [], buttons: []};
    document.querySelectorAll('input').forEach(i => {
        if(i.type === 'hidden' || i.offsetParent === null) return;
        const label = i.closest('.el-form-item')?.querySelector('label')?.textContent?.trim() || '';
        out.inputs.push({label, ph: i.placeholder || '', value: (i.value||'').slice(0,60), cls: i.className.slice(0,40)});
    });
    document.querySelectorAll('textarea').forEach(t => {
        if(t.offsetParent === null) return;
        const label = t.closest('.el-form-item')?.querySelector('label')?.textContent?.trim() || '';
        out.textareas.push({label, ph: t.placeholder || '', len: (t.value||'').length, preview: (t.value||'').slice(0,80)});
    });
    document.querySelectorAll('[contenteditable=true], .ql-editor, .w-e-text, .tox-edit-area').forEach(e => {
        out.editors.push({cls: e.className.slice(0,60), len: (e.innerText||'').length, preview: (e.innerText||'').slice(0,80)});
    });
    document.querySelectorAll('button').forEach(b => {
        if(b.offsetParent === null) return;
        const t = b.textContent.trim();
        if(t && t.length < 12) out.buttons.push(t);
    });
    return JSON.stringify(out);
})()""")
d = json.loads(info)
print("URL:", d["url"])
print("\n-- INPUTS --")
for i in d["inputs"]: print(f"  [{i['label']}] ph={i['ph']!r} val={i['value']!r}")
print("\n-- TEXTAREAS --")
for t in d["textareas"]: print(f"  [{t['label']}] len={t['len']} {t['preview']!r}")
print("\n-- RICH EDITORS --")
for e in d["editors"]: print(f"  {e['cls']} len={e['len']} {e['preview']!r}")
print("\n-- BUTTONS --")
print(" ", d["buttons"])
p.close()
