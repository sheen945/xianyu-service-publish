# -*- coding: utf-8 -*-
"""
ed_card.py - 卡券系统自动化（卡卷列表 + 卡种管理）

页面：https://ed.weeeg.com/ekadmin/card/card_cdk
子菜单：卡卷列表 / 卡种管理（SPA 内嵌路由，无独立 URL）

卡卷列表结构：
  筛选：卡种分类 / 搜索
  标签：全部 / 未使用 / 已使用 / 使用中
  按钮：添加卡卷 / 批量操作
  表格列：ID / 卡卷名称 / 卡类 / 卡号 / 卡密 / 状态 / 购买订单ID / 使用人 / 使用时间 / 创建时间 / 操作

「卡密添加」弹窗：
  字段：卡种名称 (input，可输入或选择)
  按钮：取消 / 确定
  下一步才到多卡密批量上传

用法：
    from ed_card import EDCard
    card = EDCard()
    card.connect()
    cards = card.list_cards()
    card.open_add_card()  # 打开添加卡卷弹窗
"""

import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp_tools import EDClient

CARD_URL = "https://ed.weeeg.com/ekadmin/card/card_cdk"


class EDCard(EDClient):
    """卡券系统自动化客户端"""

    def open_card_page(self):
        """打开卡卷列表页"""
        self.navigate(CARD_URL, wait=6)
        self.clear_loading_masks()
        self.wait_for_rows(timeout=15)

    def switch_to_kind_manage(self):
        """点击左侧「卡种管理」（SPA 路由切换）"""
        return self.eval("""(() => {
            const items = document.querySelectorAll('.el-menu-item, [class*=menu-item]');
            const k = [...items].find(i => i.textContent.trim() === '卡种管理' && i.offsetParent !== null);
            if(!k) return 'NOT_FOUND';
            const r = k.getBoundingClientRect();
            return JSON.stringify({x: Math.round(r.left + r.width/2), y: Math.round(r.top + r.height/2)});
        })()""")

    # ---------- 只读 ----------

    def list_cards(self, status="全部", max_rows=50):
        """读取卡卷列表
        status: 全部 / 未使用 / 已使用 / 使用中
        """
        self.open_card_page()
        if status and status != "全部":
            # 点击对应 tab
            pos = self.eval(f"""(() => {{
                const tabs = document.querySelectorAll('.el-tabs__item');
                const t = [...tabs].find(t => t.textContent.trim() === '{status}');
                if(!t) return 'NO_TAB';
                const r = t.getBoundingClientRect();
                return JSON.stringify({{x: Math.round(r.left + r.width/2), y: Math.round(r.top + r.height/2)}});
            }})()""")
            try:
                c = json.loads(pos)
                self.mouse_click(c["x"], c["y"])
                self.sleep(2)
            except Exception:
                pass
        res = self.eval(f"""(() => {{
            const rows = document.querySelectorAll('.el-table__body-wrapper .el-table__row');
            return JSON.stringify([...rows].slice(0, {max_rows}).map((row, idx) => {{
                const cells = row.querySelectorAll('td .cell');
                const text = i => cells[i] ? cells[i].textContent.trim() : '';
                return {{
                    idx: idx,
                    id: text(1),
                    name: text(2),
                    kind: text(3),
                    no: text(4),
                    secret: text(5).substring(0, 5) + '***',  # 脱敏
                    status: text(6),
                    order_id: text(7),
                    used_by: text(8),
                    used_at: text(9),
                    created_at: text(10)
                }};
            }}));
        }})()""")
        try:
            return json.loads(res)
        except Exception:
            return [{"error": res[:300]}]

    def get_card_summary(self):
        """卡卷汇总统计"""
        self.open_card_page()
        return self.eval("""(() => {
            const tabs = document.querySelectorAll('.el-tabs__item');
            const out = {};
            for(const t of tabs) {
                out[t.textContent.trim()] = {
                    active: t.classList.contains('is-active'),
                    text: t.textContent.trim()
                };
            }
            // 读分页器
            const p = document.querySelector('.el-pagination__total, .el-pagination');
            return {tabs: out, total: p ? p.textContent.replace(/\\n/g,' ').trim().substring(0,80) : 'NO_PAGINATION'};
        })()""")

    # ---------- 写操作 ----------

    def open_add_card(self, dismiss_email=True):
        """打开添加卡卷弹窗（会自动跳过绑定邮箱）"""
        self.open_card_page()
        if dismiss_email:
            # 先点添加看是否会弹邮箱
            pass
        self.click_button("添加卡卷")
        self.sleep(2.5)
        dlg = self.get_visible_dialogs()
        if "绑定邮箱" in dlg:
            # 关掉绑定邮箱
            self._close_email_bind()
            time.sleep = 1
            self.click_button("添加卡卷")
            self.sleep(3)
        return self.get_visible_dialogs()

    def _close_email_bind(self):
        """关闭绑定邮箱弹窗"""
        pos = self.eval("""(() => {
            const ds = document.querySelectorAll('.el-dialog');
            for(const d of ds) {
                const title = d.querySelector('.el-dialog__title');
                const isVis = (() => { let n=d; while(n) { const st=getComputedStyle(n); if(st.display==='none'||st.visibility==='hidden') return false; n=n.parentElement; if(n===document.body) break; } return true; })();
                if(title && title.textContent.includes('绑定') && isVis) {
                    const c = d.querySelector('.el-dialog__headerbtn');
                    if(c) { const r=c.getBoundingClientRect(); return JSON.stringify({x:Math.round(r.left+r.width/2), y:Math.round(r.top+r.height/2)}); }
                }
            }
            return 'NONE';
        })()""")
        try:
            c = json.loads(pos)
            self.mouse_click(c["x"], c["y"])
            return "CLOSED"
        except:
            return pos

    def fill_card_kind_name(self, kind_name, dry_run=False):
        """在「卡密添加」弹窗中输入卡种名称"""
        dlg = self.get_visible_dialogs()
        if "卡密添加" not in dlg:
            return f"NO_CARD_ADD_DIALOG: {dlg[:200]}"
        # 找卡种名称 input
        pos = self.eval("""(() => {
            const dlg = [...document.querySelectorAll('.el-dialog')].find(d => {
                const t = d.querySelector('.el-dialog__title');
                return t && t.textContent.includes('卡密添加');
            });
            if(!dlg) return 'NO_DIALOG';
            dlg.id = '__ed_card_dlg__';
            const input = dlg.querySelector('.el-input__inner');
            if(!input) return 'NO_INPUT';
            const r = input.getBoundingClientRect();
            return JSON.stringify({x: Math.round(r.left + r.width/2), y: Math.round(r.top + r.height/2)});
        })()""")
        try:
            c = json.loads(pos)
        except Exception:
            return f"COORD_ERR: {pos}"
        self.mouse_click(c["x"], c["y"])
        self.sleep(0.3)
        kn = json.dumps(kind_name, ensure_ascii=False)
        self.eval(f"""(() => {{
            const dlg = document.getElementById('__ed_card_dlg__');
            const input = dlg.querySelector('.el-input__inner');
            input.focus();
            document.execCommand('insertText', false, {kn});
            input.dispatchEvent(new Event('input', {{bubbles:true}}));
            return 'OK';
        }})()""")
        self.sleep(0.5)
        if dry_run:
            self.screenshot(r"C:\Users\Administrator\wbt\screen_card.png")
            return f"DRY_RUN: 卡种名称='{kind_name}' 已填入, 未点确定"
        # 点确定
        ok_pos = self.eval("""(() => {
            const dlg = document.getElementById('__ed_card_dlg__');
            const btns = dlg.querySelectorAll('.el-button');
            for(const b of btns) {
                if(b.textContent.trim() === '确 定' || b.textContent.trim() === '确定') {
                    const r = b.getBoundingClientRect();
                    return JSON.stringify({x: Math.round(r.left + r.width/2), y: Math.round(r.top + r.height/2)});
                }
            }
            return 'NO_BTN';
        })()""")
        try:
            c2 = json.loads(ok_pos)
            self.mouse_click(c2["x"], c2["y"])
            self.sleep(2)
            return f"CONFIRMED: '{kind_name}'"
        except:
            return ok_pos

    def close_add_card_dialog(self):
        """关闭卡密添加弹窗"""
        pos = self.eval("""(() => {
            const dlg = document.getElementById('__ed_card_dlg__');
            if(!dlg) return 'NO_DIALOG';
            const close = dlg.querySelector('.el-dialog__headerbtn');
            if(close) { const r = close.getBoundingClientRect(); return JSON.stringify({x:Math.round(r.left+r.width/2), y:Math.round(r.top+r.height/2)}); }
            return 'NO_CLOSE';
        })()""")
        try:
            c = json.loads(pos)
            self.mouse_click(c["x"], c["y"])
            self.sleep(1)
            return "CLOSED"
        except:
            return "FAILED"


# 修复 open_add_card 里的 bug（time.sleep 误用）
def _fixed_open_add_card(self, dismiss_email=True):
    """打开添加卡卷弹窗（会自动跳过绑定邮箱）"""
    import time as _t
    self.open_card_page()
    self.click_button("添加卡卷")
    self._t = _t
    _t.sleep(2.5)
    dlg = self.get_visible_dialogs()
    if "绑定邮箱" in dlg:
        self._close_email_bind()
        _t.sleep(1)
        self.click_button("添加卡卷")
        _t.sleep(3)
    return self.get_visible_dialogs()
EDCard.open_add_card = _fixed_open_add_card


if __name__ == "__main__":
    card = EDCard()
    card.connect()
    print("=== 1. 卡卷列表 ===")
    cards = card.list_cards()
    print(f"  共 {len(cards) if isinstance(cards, list) else 'N/A'} 条")
    for c in (cards if isinstance(cards, list) else []):
        if "error" in c:
            print("  ERROR:", c["error"])
            break
        print(f"  #{c['idx']} [{c['id']}] {c['name']} | {c['kind']} | 状态={c['status']} | 卡号={c['no']}")
    print("\n=== 2. 汇总 ===")
    print(card.get_card_summary())
    print("\n=== 3. dry_run 添加卡种 ===")
    dlg = card.open_add_card()
    print("弹窗:", dlg)
    if "卡密添加" in dlg:
        print(card.fill_card_kind_name("试用资料包", dry_run=True))
        print(card.close_add_card_dialog())
    card.close()
    print("\n=== 完成 ===")
