# -*- coding: utf-8 -*-
"""
ed_collect.py - 商品采集自动化（从自己/官方/其他闲鱼店铺采集商品）

页面：https://ed.weeeg.com/ekadmin/product/productcollect
子页：采集日志 / 商品草稿

结构：
  查询类型 radio: 0店铺商品 1官方商品 2指定其他店铺
  店铺账号 select（全部店铺=申璧诚945）
  关键词 input（商品关键词，可选）
  采集全部 select（是/否）
  按钮: 搜索 / 重置 / 批量添加到采集列表

  批量采集配置：
    商品ID列表 textarea（逗号/空格/换行分隔）
    采集平台 select（闲鱼）
    同步发货 checkbox
    鱼小铺 checkbox
    自定义配置 radio: 使用默认配置/使用自定义配置
    发布店铺 select
    发布方式 radio: 立即发布/存草稿
    按钮: 开始采集 / 重置

用法：
    from ed_collect import EDCollect
    c = EDCollect()
    c.connect()
    results = c.search_products(keyword="拍摄")     # 搜索商品
    c.collect_by_ids("1077487223816, 1079912988993")  # 按商品ID批量采集
"""

import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp_tools import EDClient

COLLECT_URL = "https://ed.weeeg.com/ekadmin/product/productcollect"


class EDCollect(EDClient):
    """商品采集自动化客户端"""

    def open_collect_page(self):
        """打开商品采集页"""
        self.navigate(COLLECT_URL, wait=6)
        self.clear_loading_masks()
        # 等待采集结果表格加载（表格可能为空，等待查询区就绪即可）
        self.wait_for_selector(".el-form, .optimized-id-textarea, [class*=collect]", timeout=15)
        self.sleep(1)

    # ---------- 查询 ----------

    def set_query_type(self, qtype="店铺商品"):
        """设置查询类型：店铺商品/官方商品/指定其他店铺"""
        coord = self.eval(f"""(() => {{
            const groups = document.querySelectorAll('.el-radio-group');
            for(const g of groups) {{
                const rbs = [...g.querySelectorAll('.el-radio-button, .el-radio')];
                const hit = rbs.find(r => r.textContent.trim() === '{qtype}');
                if(hit) {{
                    const rect = hit.getBoundingClientRect();
                    return JSON.stringify({{x: Math.round(rect.left + rect.width/2), y: Math.round(rect.top + rect.height/2)}});
                }}
            }}
            return 'NOT_FOUND';
        }})()""")
        try:
            c = json.loads(coord)
            self.mouse_click(c["x"], c["y"])
            self.sleep(0.5)
            return "SET_" + qtype
        except Exception:
            return coord

    def set_keyword(self, keyword):
        """在商品关键词输入框填入关键词"""
        # 找查询区的关键词输入框
        pos = self.eval("""(() => {
            const inputs = document.querySelectorAll('.el-input__inner');
            for(const i of inputs) {
                if(i.placeholder && i.placeholder.includes('关键词') && i.offsetParent !== null) {
                    const r = i.getBoundingClientRect();
                    return JSON.stringify({x: Math.round(r.left + r.width/2), y: Math.round(r.top + r.height/2)});
                }
            }
            return 'NOT_FOUND';
        })()""")
        try:
            c = json.loads(pos)
            self.mouse_click(c["x"], c["y"])
            self.sleep(0.3)
            # 用 JS 设置输入框值（Element UI）
            kw = json.dumps(keyword, ensure_ascii=False)
            self.eval(f"""(() => {{
                const inputs = document.querySelectorAll('.el-input__inner');
                const input = [...inputs].find(i => i.placeholder && i.placeholder.includes('关键词') && i.offsetParent !== null);
                if(!input) return 'NO_INPUT';
                const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
                setter.call(input, {kw});
                input.dispatchEvent(new Event('input', {{bubbles:true}}));
                input.dispatchEvent(new Event('change', {{bubbles:true}}));
                return 'SET_OK';
            }})()""")
            self.sleep(0.5)
            return "KEYWORD_SET"
        except Exception:
            return pos

    def search(self, keyword=None, qtype="店铺商品", click_search=True):
        """按关键词搜索"""
        self.open_collect_page()
        if qtype != "店铺商品":
            self.set_query_type(qtype)
        if keyword:
            self.set_keyword(keyword)
        if click_search:
            self.click_button("搜索")
            self.sleep(4)
            self.clear_loading_masks()
        return self.get_search_results()

    def get_search_results(self, max_rows=50):
        """读取搜索结果表格"""
        res = self.eval(f"""(() => {{
            const rows = document.querySelectorAll('.el-table__body-wrapper .el-table__row');
            return JSON.stringify([...rows].slice(0, {max_rows}).map((row, idx) => {{
                const cells = row.querySelectorAll('td .cell');
                const text = i => cells[i] ? cells[i].textContent.trim() : '';
                // 商品ID在 col1，名称在 col3，价格 col4
                return {{
                    idx: idx,
                    shop: text(1),
                    product_id: text(2).replace('商品ID','').trim(),
                    title: text(3).substring(0,80),
                    price: text(4),
                    published: text(8)
                }};
            }}));
        }})()""")
        try:
            return json.loads(res)
        except Exception:
            return [{"error": res[:300]}]

    # ---------- 采集列表 ----------

    def select_result_row(self, row_idx, checked=True):
        """勾选搜索结果中的某行"""
        flag = "true" if checked else "false"
        return self.eval(f"""(() => {{
            const rows = document.querySelectorAll('.el-table__body-wrapper .el-table__row');
            const row = rows[{row_idx}];
            if(!row) return 'NO_ROW';
            const cb = row.querySelector('.el-checkbox');
            if(!cb) return 'NO_CHECKBOX';
            const isChecked = cb.classList.contains('is-checked');
            if({flag} !== isChecked) cb.click();
            return 'OK';
        }})()""")

    def batch_add_to_list(self):
        """批量添加到采集列表（需先勾选）"""
        self.clear_loading_masks()
        res = self.click_button("批量添加到采集列表")
        self.sleep(2)
        return res

    def add_single_to_list(self, row_idx):
        """单行添加到采集列表（点行内「添加到采集列表」按钮）"""
        res = self.eval(f"""(() => {{
            const rows = document.querySelectorAll('.el-table__body-wrapper .el-table__row');
            const row = rows[{row_idx}];
            if(!row) return 'NO_ROW';
            const btn = [...row.querySelectorAll('button, .el-button')]
                .find(b => b.textContent.includes('添加到采集列表'));
            if(!btn) return 'NO_BTN';
            const r = btn.getBoundingClientRect();
            return JSON.stringify({{x: Math.round(r.left + r.width/2), y: Math.round(r.top + r.height/2)}});
        }})()""")
        try:
            c = json.loads(res)
            self.mouse_click(c["x"], c["y"])
            self.sleep(1.5)
            return "ADDED"
        except Exception:
            return res

    # ---------- 批量ID采集 ----------

    def collect_by_ids(self, ids, publish_mode="立即发布", dry_run=False):
        """
        按商品ID列表批量采集（核心功能）
        ids: 字符串或列表，如 "1077487223816,1079912988993" 或 [id1, id2]
        publish_mode: 立即发布 / 存草稿
        dry_run: True 只填ID不点开始采集
        """
        self.open_collect_page()
        if isinstance(ids, (list, tuple)):
            ids = ", ".join(str(i) for i in ids)
        # 1. 填入 textarea
        pos = self.eval("""(() => {
            const ta = document.querySelector('.optimized-id-textarea textarea, .el-textarea__inner');
            if(!ta) return 'NO_TEXTAREA';
            const r = ta.getBoundingClientRect();
            return JSON.stringify({x: Math.round(r.left + 20), y: Math.round(r.top + 15)});
        })()""")
        try:
            c = json.loads(pos)
            self.mouse_click(c["x"], c["y"])
            self.sleep(0.3)
        except Exception:
            return pos
        # 用 execCommand 注入
        ids_json = json.dumps(ids, ensure_ascii=False)
        r = self.eval(f"""(() => {{
            const ta = document.querySelector('.optimized-id-textarea textarea');
            if(!ta) return 'NO_TA';
            ta.focus();
            document.execCommand('insertText', false, {ids_json});
            ta.dispatchEvent(new Event('input', {{bubbles:true}}));
            return 'IDS_SET';
        }})()""")
        self.sleep(1.5)
        # 2. 查看有效ID计数
        count = self.eval("document.querySelector('.optimized-count-text')?.textContent || 'N/A'")
        # 3. 设置发布方式（立即发布/存草稿）
        self.set_publish_mode(publish_mode)
        if dry_run:
            return f"DRY_RUN: IDs填好(count={count}), 发布方式={publish_mode}, 未点开始采集"
        # 4. 点开始采集
        # 找底部"开始采集"按钮（可能有滚动）
        self.clear_loading_masks()
        btn_pos = self.eval("""(() => {
            const btns = document.querySelectorAll('.el-button, button');
            const b = [...btns].find(x => x.textContent.trim() === '开始采集' && x.offsetParent !== null);
            if(!b) return 'NOT_FOUND';
            // 滚动到可见
            b.scrollIntoView({block: 'center'});
            const r = b.getBoundingClientRect();
            return JSON.stringify({x: Math.round(r.left + r.width/2), y: Math.round(r.top + r.height/2)});
        })()""")
        try:
            c = json.loads(btn_pos)
            self.mouse_click(c["x"], c["y"])
            self.sleep(4)
            return f"STARTED(count={count})"
        except Exception:
            return btn_pos

    def set_publish_mode(self, mode="立即发布"):
        """设置发布方式：立即发布 / 存草稿"""
        coord = self.eval(f"""(() => {{
            const groups = document.querySelectorAll('.el-radio-group');
            for(const g of groups) {{
                const rbs = [...g.querySelectorAll('.el-radio-button, .el-radio')];
                const hit = rbs.find(r => r.textContent.trim() === '{mode}');
                if(hit) {{
                    // 滚动到可见
                    hit.scrollIntoView({{block: 'center'}});
                    const rect = hit.getBoundingClientRect();
                    return JSON.stringify({{x: Math.round(rect.left + rect.width/2), y: Math.round(rect.top + rect.height/2)}});
                }}
            }}
            return 'NOT_FOUND';
        }})()""")
        try:
            c = json.loads(coord)
            self.mouse_click(c["x"], c["y"])
            self.sleep(0.5)
            return "MODE_SET_" + mode
        except Exception:
            return coord

    def set_collect_all(self, yes=True):
        """采集全部：是/否"""
        pass  # 默认是即可

    # ---------- 采集日志/草稿 ----------

    def goto_log(self):
        """去采集日志"""
        self.navigate("https://ed.weeeg.com/ekadmin/product/productcollectlog", wait=5)
        return self.get_page_text(1500)

    def goto_draft(self):
        """去商品草稿"""
        self.navigate("https://ed.weeeg.com/ekadmin/product/productdraft", wait=5)
        return self.get_page_text(1500)


if __name__ == "__main__":
    c = EDCollect()
    c.connect()
    print("=== 测试商品采集页 ===")
    print("URL:", c.get_url())

    print("\n=== 1. 搜索'拍摄' ===")
    results = c.search(keyword="拍摄")
    print(f"  共 {len(results) if isinstance(results, list) else 'N/A'} 条结果")
    for r in (results if isinstance(results, list) else []):
        if "error" in r:
            print(" ERROR:", r["error"])
            break
        print(f"  #{r['idx']} [{r['product_id']}] {r['title'][:40]} | {r['price']}")

    c.close()
    print("\n=== 完成 ===")
