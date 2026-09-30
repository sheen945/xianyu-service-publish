# -*- coding: utf-8 -*-
"""
ed_reply.py - 智能回复配置自动化（自动回复 + AI智能回复）

页面：
  - 自动回复：https://ed.weeeg.com/ekadmin/configuration/storereply
  - AI智能回复：需探查
  - 模板管理：https://ed.weeeg.com/ekadmin/configuration/messagemt
  - 黑名单：https://ed.weeeg.com/ekadmin/configuration/replyblack
  - 图片管理：https://ed.weeeg.com/ekadmin/configuration/replyimage

添加回复弹窗字段（8 个）：
  1. 触发方式  radio-button {0:关键词回复, 1:首次回复, 2:系统消息}
  2. 触发规则  radio-button {0:无匹配, 1:包含, 2:等于}
  3. 关键词    input（输入后回车）
  4. 内容类型  radio-button {1:文本消息, 2:图片消息, 3:文本+图片}
  5. 回复文本  textarea
  6. 适用范围  radio-button {0:全部通用, 1:指定店铺/商品}
  7. 排除商品  按钮「+ 添加排除商品」
  8. 开启状态  switch（默认 true）

用法：
    from ed_reply import EDReply
    r = EDReply()
    r.connect()
    rules = r.list_rules()
    r.add_rule({
        "trigger_type": 0,        # 关键词回复
        "match_type": 1,          # 包含
        "keywords": ["你好", "在吗"],
        "content_type": 1,        # 文本消息
        "reply_text": "您好，请稍等",
        "scope": 0,               # 全部通用
        "enabled": True
    })
"""

import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp_tools import EDClient

REPLY_URL = "https://ed.weeeg.com/ekadmin/configuration/storereply"

# 字段映射（value → 中文）
TRIGGER_TYPE = {0: "关键词回复", 1: "首次回复", 2: "系统消息"}
MATCH_TYPE = {0: "无匹配", 1: "包含", 2: "等于"}
CONTENT_TYPE = {1: "文本消息", 2: "图片消息", 3: "文本+图片"}
SCOPE_TYPE = {0: "全部通用", 1: "指定店铺/商品"}


class EDReply(EDClient):
    """智能回复自动化客户端"""

    def open_reply_page(self):
        self.navigate(REPLY_URL, wait=6)
        self.clear_loading_masks()
        self.wait_for_rows(timeout=15)

    # ---------- 只读 ----------

    def list_rules(self, max_rows=50):
        """读取回复规则列表"""
        self.open_reply_page()
        res = self.eval(f"""(() => {{
            const rows = document.querySelectorAll('.el-table__body-wrapper .el-table__row');
            return JSON.stringify([...rows].slice(0, {max_rows}).map((row, idx) => {{
                const cells = row.querySelectorAll('td .cell');
                const text = i => cells[i] ? cells[i].textContent.trim() : '';
                const sw = row.querySelectorAll('.el-switch');
                return {{
                    idx: idx,
                    id: text(1),
                    keyword: text(2),
                    type: text(3),
                    content_type: text(4),
                    match_rule: text(5),
                    products: text(6),
                    shops: text(7),
                    exclude: text(8),
                    content: text(9),
                    enabled: sw[0] ? sw[0].classList.contains('is-checked') : null
                }};
            }}));
        }})()""")
        try:
            return json.loads(res)
        except Exception:
            return [{"error": res[:300]}]

    # ---------- 写操作 ----------

    def _select_radio(self, dialog, label, value):
        """在指定弹窗中，按 label + value 选 radio-button"""
        js = f"""(() => {{
            const items = dialog.querySelectorAll('.el-form-item');
            for(const it of items) {{
                const lb = it.querySelector('.el-form-item__label');
                if(!lb || !lb.textContent.includes('{label}')) continue;
                const rbs = it.querySelectorAll('.el-radio-button');
                for(const r of rbs) {{
                    const v = r.querySelector('input')?.value;
                    if(v === '{value}') {{
                        const rect = r.getBoundingClientRect();
                        return JSON.stringify({{x: Math.round(rect.left + rect.width/2), y: Math.round(rect.top + rect.height/2)}});
                    }}
                }}
            }}
            return 'NOT_FOUND';
        }})()"""
        return dialog.eval(js)

    def open_add_dialog(self):
        """点击「添加自动回复」打开弹窗"""
        self.open_reply_page()
        self.click_button("添加自动回复")
        self.sleep(2.5)
        return self.get_visible_dialogs()

    def fill_reply_form(self, rule):
        """
        填写添加回复弹窗表单（不含「添加排除商品」「确定」）
        rule 字典字段：
          trigger_type: 0/1/2
          match_type: 0/1/2
          keywords: ["kw1","kw2",...]
          content_type: 1/2/3
          reply_text: "..."
          scope: 0/1
          enabled: True/False
        """
        # 先获取弹窗引用
        dlg_info = self.eval("""(() => {
            const ds = document.querySelectorAll('.el-dialog');
            for(const d of ds) {
                const title = d.querySelector('.el-dialog__title');
                if(!title || !title.textContent.includes('添加')) continue;
                // 给弹窗加 id 方便查找
                d.id = '__ed_reply_dlg__';
                return 'OK';
            }
            return 'NO_DIALOG';
        })()""")
        if dlg_info != "OK":
            return "NO_DIALOG"

        # 触发方式
        pos = self.eval("""(() => {
            const d = document.getElementById('__ed_reply_dlg__');
            if(!d) return 'NO_DIALOG';
            const items = d.querySelectorAll('.el-form-item');
            for(const it of items) {
                const lb = it.querySelector('.el-form-item__label');
                if(!lb || !lb.textContent.includes('触发方式')) continue;
                const rbs = it.querySelectorAll('.el-radio-button');
                for(const r of rbs) {
                    if(r.querySelector('input')?.value === '""" + str(rule.get("trigger_type", 0)) + """') {
                        const rect = r.getBoundingClientRect();
                        return JSON.stringify({x: Math.round(rect.left + rect.width/2), y: Math.round(rect.top + rect.height/2)});
                    }
                }
            }
            return 'NOT_FOUND';
        })()""")
        try:
            c = json.loads(pos)
            self.mouse_click(c["x"], c["y"])
            self.sleep(0.6)
        except Exception:
            pass

        # 触发规则
        pos = self.eval("""(() => {
            const d = document.getElementById('__ed_reply_dlg__');
            if(!d) return 'NO_DIALOG';
            const items = d.querySelectorAll('.el-form-item');
            for(const it of items) {
                const lb = it.querySelector('.el-form-item__label');
                if(!lb || !lb.textContent.includes('触发规则')) continue;
                const rbs = it.querySelectorAll('.el-radio-button');
                for(const r of rbs) {
                    if(r.querySelector('input')?.value === '""" + str(rule.get("match_type", 1)) + """') {
                        const rect = r.getBoundingClientRect();
                        return JSON.stringify({x: Math.round(rect.left + rect.width/2), y: Math.round(rect.top + rect.height/2)});
                    }
                }
            }
            return 'NOT_FOUND';
        })()""")
        try:
            c = json.loads(pos)
            self.mouse_click(c["x"], c["y"])
            self.sleep(0.6)
        except Exception:
            pass

        # 关键词：input 输入 + 回车
        keywords = rule.get("keywords", [])
        if keywords:
            pos = self.eval("""(() => {
                const d = document.getElementById('__ed_reply_dlg__');
                if(!d) return 'NO_DIALOG';
                const items = d.querySelectorAll('.el-form-item');
                for(const it of items) {
                    const lb = it.querySelector('.el-form-item__label');
                    if(!lb || !lb.textContent.includes('关键词')) continue;
                    const input = it.querySelector('.el-input__inner');
                    if(input) {
                        const r = input.getBoundingClientRect();
                        return JSON.stringify({x: Math.round(r.left + r.width/2), y: Math.round(r.top + r.height/2)});
                    }
                }
                return 'NOT_FOUND';
            })()""")
            try:
                c = json.loads(pos)
                for kw in keywords:
                    self.mouse_click(c["x"], c["y"])
                    self.sleep(0.3)
                    # 真实键盘输入 + 回车
                    self.bring_to_front()
                    import time
                    for ch in kw:
                        self.msg_id += 1
                        mid = self.msg_id
                        self.ws.send(json.dumps({
                            "id": mid,
                            "method": "Input.dispatchKeyEvent",
                            "params": {"type": "char", "text": ch}
                        }))
                        try:
                            self.ws.recv()
                        except Exception:
                            pass
                        time.sleep(0.05)
                    # 回车
                    self.msg_id += 1
                    self.ws.send(json.dumps({
                        "id": self.msg_id,
                        "method": "Input.dispatchKeyEvent",
                        "params": {"type": "keyDown", "key": "Enter", "code": "Enter", "windowsVirtualKeyCode": 13}
                    }))
                    try:
                        self.ws.recv()
                    except Exception:
                        pass
                    self.sleep(0.5)
            except Exception:
                pass

        # 内容类型
        pos = self.eval("""(() => {
            const d = document.getElementById('__ed_reply_dlg__');
            if(!d) return 'NO_DIALOG';
            const items = d.querySelectorAll('.el-form-item');
            for(const it of items) {
                const lb = it.querySelector('.el-form-item__label');
                if(!lb || !lb.textContent.includes('内容类型')) continue;
                const rbs = it.querySelectorAll('.el-radio-button');
                for(const r of rbs) {
                    if(r.querySelector('input')?.value === '""" + str(rule.get("content_type", 1)) + """') {
                        const rect = r.getBoundingClientRect();
                        return JSON.stringify({x: Math.round(rect.left + rect.width/2), y: Math.round(rect.top + rect.height/2)});
                    }
                }
            }
            return 'NOT_FOUND';
        })()""")
        try:
            c = json.loads(pos)
            self.mouse_click(c["x"], c["y"])
            self.sleep(0.6)
        except Exception:
            pass

        # 回复文本
        reply_text = rule.get("reply_text", "")
        if reply_text:
            pos = self.eval("""(() => {
                const d = document.getElementById('__ed_reply_dlg__');
                if(!d) return 'NO_DIALOG';
                const items = d.querySelectorAll('.el-form-item');
                for(const it of items) {
                    const lb = it.querySelector('.el-form-item__label');
                    if(!lb || !lb.textContent.includes('回复文本')) continue;
                    const ta = it.querySelector('.el-textarea__inner');
                    if(ta) {
                        const r = ta.getBoundingClientRect();
                        return JSON.stringify({x: Math.round(r.left + 20), y: Math.round(r.top + 15)});
                    }
                }
                return 'NOT_FOUND';
            })()""")
            try:
                c = json.loads(pos)
                self.mouse_click(c["x"], c["y"])
                self.sleep(0.3)
                # 真实键盘输入（不支持中文直接输入，需 base64 或粘贴）
                # 这里用 execCommand 方式更稳
                self.eval(f"""(() => {{
                    const d = document.getElementById('__ed_reply_dlg__');
                    const ta = d.querySelector('.el-textarea__inner');
                    if(!ta) return 'NO_TA';
                    ta.focus();
                    document.execCommand('insertText', false, {json.dumps(reply_text, ensure_ascii=False)});
                    return 'OK';
                }})()""")
                self.sleep(0.5)
            except Exception:
                pass

        # 适用范围
        pos = self.eval("""(() => {
            const d = document.getElementById('__ed_reply_dlg__');
            if(!d) return 'NO_DIALOG';
            const items = d.querySelectorAll('.el-form-item');
            for(const it of items) {
                const lb = it.querySelector('.el-form-item__label');
                if(!lb || !lb.textContent.includes('适用范围')) continue;
                const rbs = it.querySelectorAll('.el-radio-button');
                for(const r of rbs) {
                    if(r.querySelector('input')?.value === '""" + str(rule.get("scope", 0)) + """') {
                        const rect = r.getBoundingClientRect();
                        return JSON.stringify({x: Math.round(rect.left + rect.width/2), y: Math.round(rect.top + rect.height/2)});
                    }
                }
            }
            return 'NOT_FOUND';
        })()""")
        try:
            c = json.loads(pos)
            self.mouse_click(c["x"], c["y"])
            self.sleep(0.6)
        except Exception:
            pass

        # 开启状态（如果传 enabled=False，需点关掉）
        if rule.get("enabled", True) is False:
            pos = self.eval("""(() => {
                const d = document.getElementById('__ed_reply_dlg__');
                if(!d) return 'NO_DIALOG';
                const items = d.querySelectorAll('.el-form-item');
                for(const it of items) {
                    const lb = it.querySelector('.el-form-item__label');
                    if(!lb || !lb.textContent.includes('开启状态')) continue;
                    const sw = it.querySelector('.el-switch');
                    if(sw) {
                        const rect = sw.getBoundingClientRect();
                        return JSON.stringify({x: Math.round(rect.left + rect.width/2), y: Math.round(rect.top + rect.height/2)});
                    }
                }
                return 'NOT_FOUND';
            })()""")
            try:
                c = json.loads(pos)
                self.mouse_click(c["x"], c["y"])
                self.sleep(0.6)
            except Exception:
                pass

        return "FORM_FILLED"

    def click_dialog_confirm(self):
        """在打开的弹窗中点「确定」"""
        pos = self.eval("""(() => {
            const d = document.getElementById('__ed_reply_dlg__');
            if(!d) return 'NO_DIALOG';
            const btns = d.querySelectorAll('.el-button');
            for(const b of btns) {
                if(b.textContent.trim() === '确 定' || b.textContent.trim() === '确定') {
                    const r = b.getBoundingClientRect();
                    return JSON.stringify({x: Math.round(r.left + r.width/2), y: Math.round(r.top + r.height/2)});
                }
            }
            return 'NO_CONFIRM_BTN';
        })()""")
        try:
            c = json.loads(pos)
            self.mouse_click(c["x"], c["y"])
            self.sleep(2)
            return "CONFIRM_CLICKED"
        except Exception:
            return f"FAILED: {pos}"

    def close_dialog(self):
        """关闭弹窗"""
        pos = self.eval("""(() => {
            const d = document.getElementById('__ed_reply_dlg__');
            if(!d) return 'NO_DIALOG';
            const close = d.querySelector('.el-dialog__headerbtn');
            if(close) {
                const r = close.getBoundingClientRect();
                return JSON.stringify({x: Math.round(r.left + r.width/2), y: Math.round(r.top + r.height/2)});
            }
            return 'NO_CLOSE';
        })()""")
        try:
            c = json.loads(pos)
            self.mouse_click(c["x"], c["y"])
            self.sleep(1)
            return "CLOSED"
        except Exception:
            return "FAILED"

    def add_rule(self, rule, dry_run=False):
        """
        添加回复规则（完整流程：打开弹窗→填表→点确定）
        rule: 见 fill_reply_form 文档
        dry_run: True 打开填表但不点确定
        返回 "ADDED" 或错误信息
        """
        dlg = self.open_add_dialog()
        if "添加回复" not in dlg:
            return f"DIALOG_NOT_OPEN: {dlg[:200]}"
        # 填表
        fill_result = self.fill_reply_form(rule)
        if "FILLED" not in fill_result:
            return f"FILL_FAILED: {fill_result}"
        # 截图便于调试
        self.screenshot(r"C:\Users\Administrator\wbt\screen_reply_filled.png")
        if dry_run:
            return f"DRY_RUN: form filled (确定 not clicked)"
        # 点确定
        confirm = self.click_dialog_confirm()
        self.sleep(2)
        # 清理id
        self.eval("document.getElementById('__ed_reply_dlg__')?.removeAttribute('id')")
        return f"CONFIRM: {confirm}"

    def toggle_rule(self, row_idx, enabled):
        """切换某行规则的开关状态"""
        coord = self.eval(f"""(() => {{
            const rows = document.querySelectorAll('.el-table__body-wrapper .el-table__row');
            const row = rows[{row_idx}];
            if(!row) return 'NO_ROW';
            const sw = row.querySelectorAll('.el-switch')[0];
            if(!sw) return 'NO_SW';
            const r = sw.getBoundingClientRect();
            return JSON.stringify({{x: Math.round(r.left + r.width/2), y: Math.round(r.top + r.height/2), currentOn: sw.classList.contains('is-checked')}});
        }})()""")
        try:
            c = json.loads(coord)
        except Exception:
            return f"COORD_ERR: {coord}"
        if c.get("currentOn") == enabled:
            return f"ALREADY_{'ON' if enabled else 'OFF'}"
        self.clear_loading_masks()
        self.mouse_click(c["x"], c["y"])
        self.sleep(2)
        return f"TOGGLE: now {'ON' if enabled else 'OFF'}"

    def list_reply_submenu(self):
        """列出智能回复左侧子菜单"""
        return self.eval("""(() => {
            const items = document.querySelectorAll('.el-menu-item, a');
            return [...items].filter(i => i.offsetParent !== null)
                .map(i => i.textContent.trim())
                .filter(t => t && t.length < 20)
                .filter(t => ['自动回复', 'AI 智能回复', '回复配置', '模板管理', '黑名单', '图片管理', '运行日志', '通知管理', '鱼店配置'].includes(t))
                .join(' | ');
        })()""")


if __name__ == "__main__":
    r = EDReply()
    r.connect()
    print("=== 1. 当前规则列表 ===")
    rules = r.list_rules()
    print(f"  共 {len(rules) if isinstance(rules, list) else 'N/A'} 条规则")
    for rule in (rules if isinstance(rules, list) else []):
        if "error" in rule:
            print(" ERROR:", rule["error"])
            break
        print(f"  #{rule['idx']} 关键词={rule['keyword'][:20]} 类型={rule['type']} 触发={rule['match_rule']} 状态={'ON' if rule['enabled'] else 'OFF'}")
    print("\n=== 2. 左侧子菜单 ===")
    print(" ", r.list_reply_submenu())
    r.close()
    print("\n=== 完成 ===")
