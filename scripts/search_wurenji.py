# -*- coding: utf-8 -*-
"""临时脚本：在易店商品列表搜索关键词并打印结果"""
import io
import json
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from ed_product import EDProduct

KEYWORD = sys.argv[1] if len(sys.argv) > 1 else "无人机"

p = EDProduct()
p.connect()
p.open_product_page()
p.switch_status_tab("出售中")

res = p.eval(f"""(() => {{
    const inputs = document.querySelectorAll('.el-input__inner');
    const search = [...inputs].find(i => i.placeholder && i.placeholder.includes('查询') && i.offsetParent !== null);
    if(!search) return 'NO_SEARCH_INPUT: ' + [...inputs].map(i=>i.placeholder).join(',');
    const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
    setter.call(search, {json.dumps(KEYWORD, ensure_ascii=False)});
    search.dispatchEvent(new Event('input', {{bubbles:true}}));
    search.dispatchEvent(new Event('change', {{bubbles:true}}));
    return 'INPUT_SET';
}})()""")
print("搜索框:", res)
p.sleep(1)
p.click_button("查询")
p.sleep(3)

rows = p.read_current_page_rows(50)
print(f"=== 搜索「{KEYWORD}」结果 {len(rows)} 个 ===")
for prod in rows:
    if "error" in prod:
        print("ERROR:", prod["error"])
        break
    print(f"#{prod['idx']} [{prod['id']}] {prod['title']} | 价{prod['price']}")
p.close()
