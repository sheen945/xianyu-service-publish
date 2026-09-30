# -*- coding: utf-8 -*-
"""
ed_product.py - 商品管理自动化（我的商品 + 小刀商品）

页面：https://ed.weeeg.com/ekadmin/product/product_list
表格列（0-based）：
  0=checkbox 1=ID 2=店铺 3=商品信息 4=售价 5=曝光 6=浏览 7=想要
  8=自动发货开关 9=售罄自动上架开关 10=2人小刀开关 11=发布日期 12=更新时间 13=操作(更多)
行内更多菜单：配置发货/编辑商品/复制商品/下架宝贝/删除商品

状态tab：出售中的商品/已下架的商品/已经售罄商品/已配置发货/未配置发货/定时上架商品

用法：
    from ed_product import EDProduct
    p = EDProduct()
    p.list_products()                    # 读取出售中商品
    p.list_products(status="已下架的商品")
    p.set_row_switch(row_idx, "auto_ship", True)   # 开某行自动发货
    p.batch_set_switches(rows=[0,1,2], auto_ship=True, resell=True, bargain=True)
"""

import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp_tools import EDClient

PRODUCT_URL = "https://ed.weeeg.com/ekadmin/product/product_list"

# 状态 tab 映射
STATUS_TABS = {
    "出售中": "出售中的商品",
    "已下架": "已下架的商品",
    "已售罄": "已经售罄商品",
    "已配置发货": "已配置发货",
    "未配置发货": "未配置发货",
    "定时上架": "定时上架商品",
}

# 开关列映射（行内 el-switch 索引）
SWITCH_INDEX = {"auto_ship": 0, "resell": 1, "bargain": 2}
SWITCH_LABELS = {0: "自动发货", 1: "售罄自动上架", 2: "2人小刀"}


class EDProduct(EDClient):
    """商品管理自动化客户端"""

    def open_product_page(self):
        """打开商品页（强制刷新确保数据加载）"""
        # 先检查是否已在商品页且行数>0，否则刷新
        try:
            url = self.get_url()
            rows = self.eval("document.querySelectorAll('.el-table__body-wrapper .el-table__row').length")
            if "product_list" in url and rows and int(rows) > 0:
                return
        except Exception:
            pass
        if "product_list" not in (self.get_url() or ""):
            self.navigate(PRODUCT_URL, wait=6)
        self.reload(wait=6)
        self.wait_for_rows(timeout=25)

    # ---------- 只读操作 ----------

    def switch_status_tab(self, tab_key="出售中"):
        """切换状态 tab"""
        tab_text = STATUS_TABS.get(tab_key, tab_key)
        res = self.eval(f"""(() => {{
            const tabs = document.querySelectorAll('.el-tabs__item');
            const t = [...tabs].find(t => t.textContent.includes('{tab_text}') && t.offsetParent !== null);
            if(!t) return 'NOT_FOUND';
            if(!t.classList.contains('is-active')) t.click();
            return 'OK';
        }})()""")
        self.sleep(3)
        self.wait_for_rows(timeout=15)
        return res

    def read_current_page_rows(self, max_rows=50):
        """读取当前页表格数据"""
        res = self.eval(f"""(() => {{
            const rows = document.querySelectorAll('.el-table__body-wrapper .el-table__row');
            return JSON.stringify([...rows].slice(0, {max_rows}).map((row, idx) => {{
                const cells = row.querySelectorAll('td .cell');
                const text = i => cells[i] ? cells[i].textContent.trim() : '';
                const sws = row.querySelectorAll('.el-switch');
                const swOn = i => sws[i] ? sws[i].classList.contains('is-checked') : null;
                const titleEl = cells[3] ? cells[3].querySelector('span[style*="font-size: 14px"]') : null;
                const idEl = cells[3] ? [...cells[3].querySelectorAll('span')].find(s => s.textContent.includes('商品ID')) : null;
                return {{
                    idx: idx,
                    id: idEl ? idEl.textContent.replace('商品ID ','').trim() : '',
                    shop: text(2),
                    title: titleEl ? titleEl.textContent.trim() : text(3).substring(0,60),
                    price: text(4).replace(/\\n/g,'').trim(),
                    exposure: text(5),
                    views: text(6),
                    wants: text(7),
                    auto_ship: swOn(0),
                    resell: swOn(1),
                    bargain: swOn(2),
                    published: text(11),
                    updated: text(12)
                }};
            }}));
        }})()""")
        try:
            return json.loads(res)
        except Exception:
            return [{"error": res[:300]}]

    def goto_page(self, page_num):
        """跳转到指定分页"""
        res = self.eval(f"""(() => {{
            const pagers = document.querySelectorAll('.el-pager li');
            const target = [...pagers].find(li => li.textContent.trim() === '{page_num}');
            if(target) {{ target.click(); return 'PAGER_CLICKED'; }}
            // 可能是跳页输入
            const jump = document.querySelector('.el-pagination__jump input');
            if(jump) {{
                const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
                setter.call(jump, '{page_num}');
                jump.dispatchEvent(new Event('input', {{bubbles:true}}));
                jump.dispatchEvent(new Event('change', {{bubbles:true}}));
                jump.dispatchEvent(new KeyboardEvent('keyup', {{key:'Enter', code:'Enter', keyCode:13, bubbles:true}}));
                return 'JUMP_SET';
            }}
            return 'NO_PAGER';
        }})()""")
        self.sleep(3)
        return res

    def set_page_size(self, size=50):
        """设置每页条数（15/20/30/50）"""
        # 打开分页 size 下拉
        self.eval("""(() => {
            const sel = document.querySelector('.el-pagination .el-select');
            if(sel) { sel.click(); return 'OPENED'; }
            // 尝试 .el-select 元素
            const sels = document.querySelectorAll('.el-select');
            for(const s of sels) {
                if(s.offsetParent !== null && s.textContent.includes('条/页')) { s.click(); return 'OPENED'; }
            }
            return 'NO_SELECT';
        })()""")
        self.sleep(1.5)
        # 选指定大小
        res = self.eval(f"""(() => {{
            const opts = document.querySelectorAll('.el-select-dropdown__item');
            const o = [...opts].find(x => x.textContent.includes('{size}条'));
            if(o) {{ o.click(); return 'PICKED'; }}
            return 'NO_OPT:' + [...opts].map(x=>x.textContent.trim()).join(',');
        }})()""")
        self.sleep(3)
        self.wait_for_rows(timeout=15)
        return res

    def list_products(self, status="出售中", max_rows=50, max_pages=1):
        """
        读取商品列表（支持翻页）
        status: 出售中/已下架/已售罄/已配置发货/未配置发货/定时上架
        max_pages: 最多翻几页（默认1页）
        """
        self.open_product_page()
        if status:
            self.switch_status_tab(status)
        # 尝试放大每页到50条减少翻页
        all_products = []
        for page in range(1, max_pages + 1):
            if page > 1:
                self.goto_page(page)
            rows_data = self.read_current_page_rows(max_rows)
            if not rows_data:
                break
            if "error" in rows_data[0]:
                if all_products:
                    break
                return rows_data
            all_products.extend(rows_data)
            # 检查是否还有下一页（当前页满才可能继续）
            if len(rows_data) < 15:
                break
        return all_products

    def count_pages(self):
        """获取总条数和总页数"""
        return self.eval("""(() => {
            const page = document.querySelector('.el-pagination');
            if(!page) return 'NO_PAGINATION';
            return page.textContent.trim().replace(/\\n/g,' ');
        })()""")

    def search_product(self, keyword, status="出售中"):
        """按关键词搜索商品"""
        self.open_product_page()
        if status:
            self.switch_status_tab(status)
        # 搜索框：店铺旁的搜索输入
        res = self.eval(f"""(() => {{
            const inputs = document.querySelectorAll('.el-input__inner');
            const search = [...inputs].find(i => i.placeholder && i.placeholder.includes('搜索') && i.offsetParent !== null);
            if(!search) return 'NO_SEARCH_INPUT: ' + [...inputs].map(i=>i.placeholder).join(',');
            const proto = HTMLInputElement.prototype;
            const setter = Object.getOwnPropertyDescriptor(proto, 'value').set;
            setter.call(search, {json.dumps(keyword, ensure_ascii=False)});
            search.dispatchEvent(new Event('input', {{bubbles:true}}));
            search.dispatchEvent(new Event('change', {{bubbles:true}}));
            return 'INPUT_SET';
        }})()""")
        self.sleep(1)
        # 点查询按钮
        self.click_button("查询")
        self.sleep(3)
        return res

    # ---------- 行操作 ----------

    def set_row_switch(self, row_idx, switch_name, enabled=True):
        """
        设置指定行开关
        row_idx: 行索引(0开始)
        switch_name: auto_ship(自动发货) / resell(售罄上架) / bargain(2人小刀)
        """
        si = SWITCH_INDEX.get(switch_name)
        if si is None:
            return f"INVALID_SWITCH: {switch_name}"
        # 先清除遮罩
        self.clear_loading_masks()
        flag = "true" if enabled else "false"
        res = self.eval(f"""(() => {{
            const rows = document.querySelectorAll('.el-table__body-wrapper .el-table__row');
            const row = rows[{row_idx}];
            if(!row) return 'NO_ROW';
            const sws = row.querySelectorAll('.el-switch');
            const sw = sws[{si}];
            if(!sw) return 'NO_SWITCH';
            const isOn = sw.classList.contains('is-checked');
            if({flag} !== isOn) {{
                const core = sw.querySelector('.el-switch__core');
                if(core) core.click();
                else sw.click();
            }}
            return 'SWITCHED';
        }})()""")
        self.sleep(2)
        # 再次清除遮罩，处理可能的弹窗
        self.clear_loading_masks()
        dlg = self.get_visible_dialogs()
        if dlg != "NO_VISIBLE_DIALOG":
            return f"SWITCHED_WITH_DIALOG: {dlg[:300]}"
        # 验证结果
        verify = self.eval(f"""(() => {{
            const rows = document.querySelectorAll('.el-table__body-wrapper .el-table__row');
            const row = rows[{row_idx}];
            if(!row) return 'NO_ROW';
            const sws = row.querySelectorAll('.el-switch');
            return sws[{si}] ? sws[{si}].classList.contains('is-checked') : null;
        }})()""")
        return f"SWITCHED, now_on={verify}"

    def set_all_row_switches(self, row_idx, auto_ship=None, resell=None, bargain=None):
        """设置指定行的多个开关（None 表示不动）"""
        changes = []
        if auto_ship is not None:
            changes.append(f"auto_ship={self.set_row_switch(row_idx,'auto_ship',auto_ship)}")
        if resell is not None:
            changes.append(f"resell={self.set_row_switch(row_idx,'resell',resell)}")
        if bargain is not None:
            changes.append(f"bargain={self.set_row_switch(row_idx,'bargain',bargain)}")
        return changes

    def batch_set_switches(self, rows, auto_ship=None, resell=None, bargain=None, confirm=True):
        """
        批量设置多行的开关（每行间隔）
        rows: 行索引列表 [0,1,2,...]
        """
        self.open_product_page()
        results = []
        for r in rows:
            r_ = self.set_all_row_switches(r, auto_ship, resell, bargain)
            results.append(f"行{r}: {r_}")
            self.sleep(1.5)  # 防抖
        return results

    # ---------- 批量操作 ----------

    def batch_action(self, rows, action="上下架", dry_run=True):
        """
        批量操作：上下架/删除/复制/设置
        rows: 行索引列表
        action: 上下架 / 删除 / 复制 / 设置
        dry_run: True 只勾选不执行（安全预览）
        """
        self.open_product_page()
        # 1. 勾选指定行
        for r in rows:
            self.check_row(r, True)
            self.sleep(0.5)
        self.sleep(1)
        # 2. 获取勾选状态
        checked = self.get_checked_count()
        if dry_run:
            return {"status": "DRY_RUN", "checked": checked, "note": "已勾选但未执行，如需执行请设 dry_run=False"}
        # 3. 点击对应批量按钮
        btn_map = {"上下架": "批量上下架", "删除": "批量删除", "复制": "批量复制", "设置": "批量设置"}
        btn_text = btn_map.get(action, action)
        res = self.click_button(btn_text)
        self.sleep(2)
        dlg = self.get_visible_dialogs()
        return {"status": res, "checked": checked, "dialog": dlg}

    # ---------- 行内更多菜单 ----------

    def row_more(self, row_idx=0, menu_item=None):
        """
        点击行内「更多」下拉菜单
        menu_item: 配置发货/编辑商品/复制商品/下架宝贝/删除商品
        """
        # 先横向滚动表格让操作列可见
        self.eval("""(() => {
            const cs = document.querySelectorAll('.el-table__body-wrapper, .el-table__fixed-right, .el-table__fixed, .el-scrollbar__wrap');
            for(const c of cs) { if(c.scrollWidth > c.clientWidth + 5) c.scrollLeft = c.scrollWidth; }
            return 'SCROLLED';
        })()""")
        self.sleep(1.5)
        # 获取「更多」坐标
        coord = self.eval(f"""(() => {{
            const rows = document.querySelectorAll('.el-table__body-wrapper .el-table__row');
            const row = rows[{row_idx}];
            if(!row) return 'NO_ROW';
            const link = row.querySelector('.el-dropdown-selfdefine');
            if(!link) return 'NO_DROPDOWN_LINK';
            const r = link.getBoundingClientRect();
            return JSON.stringify({{x: Math.round(r.left + r.width/2), y: Math.round(r.top + r.height/2)}});
        }})()""")
        try:
            import json
            c = json.loads(coord)
        except Exception:
            return f"COORD_ERR: {coord}"
        # 真实鼠标 hover
        self.mouse_hover(c["x"], c["y"], wait=1.5)
        if menu_item is None:
            return self.read_visible_dropdown_menus()
        # 找到菜单项坐标并点击
        res = self.eval(f"""(() => {{
            const menus = document.querySelectorAll('.el-dropdown-menu, .el-popper');
            for(const m of menus) {{
                const st = getComputedStyle(m);
                if(st.display !== 'none' && st.visibility !== 'hidden' && m.offsetParent !== null) {{
                    const items = [...m.querySelectorAll('.el-dropdown-menu__item')];
                    const item = items.find(i => i.textContent.includes('{menu_item}'));
                    if(item) {{
                        const r = item.getBoundingClientRect();
                        return JSON.stringify({{x: Math.round(r.left + r.width/2), y: Math.round(r.top + r.height/2)}});
                    }}
                }}
            }}
            return 'MENU_NOT_VISIBLE';
        }})()""")
        try:
            mc = json.loads(res)
        except Exception:
            return f"MENU_NOT_FOUND: {res}"
        self.mouse_click(mc["x"], mc["y"])
        self.sleep(2)
        return f"CLICKED_{menu_item}"

    def open_config_ship_dialog(self, row_idx=0):
        """
        点击行内「自动发货」开关 → 弹「配置发货」对话框
        重要：行内 el-switch 点击不会直接 toggle 状态，而是打开配置发货弹窗
        """
        coord = self.eval(f"""(() => {{
            const row = document.querySelectorAll('.el-table__body-wrapper .el-table__row')[{row_idx}];
            if(!row) return 'NO_ROW';
            const core = row.querySelectorAll('.el-switch')[0].querySelector('.el-switch__core');
            const r = core.getBoundingClientRect();
            return JSON.stringify({{x: Math.round(r.left + r.width/2), y: Math.round(r.top + r.height/2)}});
        }})()""")
        try:
            import json
            c = json.loads(coord)
        except Exception:
            return f"COORD_ERR: {coord}"
        self.clear_loading_masks()
        self.mouse_click(c["x"], c["y"])
        self.sleep(2.5)
        dlg = self.get_visible_dialogs()
        if "配置发货" in dlg:
            return "CONFIG_DIALOG_OPENED"
        return f"NO_DIALOG: {dlg}"

    # ---------- 组合命令 ----------

    def view_switch_overview(self, max_rows=50):
        """查看当前商品列表的所有开关配置总览"""
        products = self.list_products(status="出售中", max_rows=max_rows)
        if not products or "error" in products[0]:
            return products
        stats = {"auto_ship_on": 0, "resell_on": 0, "bargain_on": 0}
        for p in products:
            if p.get("auto_ship"): stats["auto_ship_on"] += 1
            if p.get("resell"): stats["resell_on"] += 1
            if p.get("bargain"): stats["bargain_on"] += 1
        total = len(products)
        return {
            "total": total,
            "stats": stats,
            "products": products
        }


if __name__ == "__main__":
    p = EDProduct()
    p.connect()
    print("=== 出售中商品列表（前10个） ===")
    products = p.list_products(status="出售中", max_rows=10)
    for prod in products:
        if "error" in prod:
            print("ERROR:", prod["error"])
            break
        print(f"#{prod['idx']} [{prod['id']}] {prod['title'][:30]} | 价{prod['price']} | 自动发货:{prod['auto_ship']} 售罄上架:{prod['resell']} 小刀:{prod['bargain']}")
    p.close()
