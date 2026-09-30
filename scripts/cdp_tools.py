# -*- coding: utf-8 -*-
"""
cdp_tools.py - 易店助手（ed.weeeg.com）CDP 通用操作工具库
基于 Python + websocket-client 直连 Chrome CDP（端口 9222）
用法：
    from cdp_tools import EDClient
    ed = EDClient()
    ed.connect()          # 自动找到易店助手标签页
    ed.navigate(url)      # 导航
    data = ed.read_table() # 读取 el-table 数据
"""

import json
import os
import time
import requests
import websocket

CDP_URL = "http://127.0.0.1:9222"
ED_PATTERN = "ed.weeeg.com/ekadmin"


class EDClient:
    """易店助手 CDP 客户端"""

    def __init__(self, port=9222):
        self.cdp_url = f"http://127.0.0.1:{port}"
        self.ws = None
        self.msg_id = 0
        self.target_url = ""

    # ---------- 连接 ----------

    def connect(self, url_pattern=ED_PATTERN):
        """连接易店助手标签页"""
        tabs = requests.get(f"{self.cdp_url}/json/list", timeout=5).json()
        target = None
        for t in tabs:
            if url_pattern in t.get("url", ""):
                target = t
                break
        if not target:
            raise Exception("未找到易店助手标签页，请确认 Chrome 已用 CDP 端口打开 ed.weeeg.com")
        # Chrome 152+ 会拒绝不带 Origin 头的 WS 握手（403），这里固定带一个本地 Origin
        try:
            self.ws = websocket.create_connection(
                target["webSocketDebuggerUrl"], timeout=20,
                origin=self.cdp_url, suppress_origin=False)
        except Exception:
            self.ws = websocket.create_connection(
                target["webSocketDebuggerUrl"], timeout=20, suppress_origin=True)
        self.target_url = target.get("url", "")
        # 关键：激活标签页到前台，否则 CDP 模拟鼠标事件不生效！
        self.bring_to_front()
        return target

    def reconnect(self):
        """断线重连"""
        try:
            if self.ws:
                self.ws.close()
        except Exception:
            pass
        self.ws = None
        self.connect()

    def close(self):
        if self.ws:
            try:
                self.ws.close()
            except Exception:
                pass

    def bring_to_front(self):
        """把标签页激活到前台（必须！后台标签页 CDP 鼠标事件会被丢弃）"""
        try:
            self.msg_id += 1
            mid = self.msg_id
            self.ws.send(json.dumps({
                "id": mid,
                "method": "Page.bringToFront"
            }))
            deadline = time.time() + 5
            while time.time() < deadline:
                r = json.loads(self.ws.recv())
                if r.get("id") == mid:
                    break
        except Exception:
            pass
        time.sleep(0.5)

    def mouse_click(self, x, y, double=False):
        """真实鼠标点击指定坐标（需要页面在前台）"""
        self.bring_to_front()
        click_count = 2 if double else 1
        for et, extra in [
            ("mouseMoved", {}),
            ("mousePressed", {"button": "left", "clickCount": click_count}),
            ("mouseReleased", {"button": "left", "clickCount": click_count}),
        ]:
            params = {"type": et, "x": x, "y": y}
            params.update(extra)
            self.msg_id += 1
            mid = self.msg_id
            self.ws.send(json.dumps({
                "id": mid,
                "method": "Input.dispatchMouseEvent",
                "params": params
            }))
            try:
                json.loads(self.ws.recv())
            except Exception:
                pass
            time.sleep(0.3)
        time.sleep(1)

    def mouse_hover(self, x, y, wait=1.5):
        """真实鼠标悬停（不发click，触发 hover 事件如 el-dropdown）"""
        self.bring_to_front()
        self.msg_id += 1
        mid = self.msg_id
        self.ws.send(json.dumps({
            "id": mid,
            "method": "Input.dispatchMouseEvent",
            "params": {"type": "mouseMoved", "x": x, "y": y}
        }))
        try:
            json.loads(self.ws.recv())
        except Exception:
            pass
        time.sleep(wait)

    def read_visible_dropdown_menus(self):
        """读取当前可见的 el-dropdown-menu（含 transfer 到 body 的）"""
        return self.eval("""(() => {
            const menus = document.querySelectorAll('.el-dropdown-menu, .el-popper, [class*=dropdown-menu]');
            const out = [];
            for(const m of menus) {
                const st = getComputedStyle(m);
                if(st.display !== 'none' && st.visibility !== 'hidden' && m.offsetParent !== null) {
                    const items = [...m.querySelectorAll('.el-dropdown-menu__item, [class*=dropdown-item]')]
                        .map(i => i.textContent.trim()).filter(t => t);
                    if(items.length > 0) {
                        out.push('MENU[' + items.join(' | ') + ']');
                    }
                }
            }
            return out.length ? out.join(' || ') : 'NO_VISIBLE_DROPDOWN';
        })()""")

    def element_center(self, js_expr_returning_el):
        """获取元素中心坐标。传入一个JS表达式，返回元素引用（用 !! 包装成布尔）
        实际用法：先 eval 拿坐标，再用 mouse_click"""
        pass

    def click_element_coords(self, selector):
        """获取元素坐标并真实点击"""
        res = self.eval(f"""(() => {{
            const el = document.querySelector('{selector}');
            if(!el) return 'NOT_FOUND';
            const r = el.getBoundingClientRect();
            if(r.width === 0) return 'ZERO_SIZE';
            return JSON.stringify({{x: Math.round(r.left + r.width/2), y: Math.round(r.top + r.height/2)}});
        }})()""")
        try:
            c = json.loads(res)
            self.mouse_click(c["x"], c["y"])
            return "CLICKED"
        except Exception:
            return res

    # ---------- 基础操作 ----------

    def eval(self, expression, timeout=15):
        """执行 JS 表达式并返回值"""
        self.msg_id += 1
        mid = self.msg_id
        self.ws.send(json.dumps({
            "id": mid,
            "method": "Runtime.evaluate",
            "params": {"expression": expression, "returnByValue": True}
        }))
        while True:
            r = json.loads(self.ws.recv())
            if r.get("id") != mid:
                continue
            if "error" in r:
                return f"CDP_ERROR: {json.dumps(r['error'], ensure_ascii=False)}"
            return r.get("result", {}).get("result", {}).get("value", "")

    def navigate(self, url, wait=4):
        """导航到指定 URL（SPA 页面建议 wait>=6）"""
        self.msg_id += 1
        mid = self.msg_id
        self.ws.send(json.dumps({
            "id": mid,
            "method": "Page.navigate",
            "params": {"url": url}
        }))
        # 等待导航响应
        deadline = time.time() + 10
        while time.time() < deadline:
            try:
                r = json.loads(self.ws.recv())
                if r.get("id") == mid:
                    break
            except Exception:
                break
        time.sleep(wait)
        # 额外等待页面完全加载
        self.eval("new Promise(r => setTimeout(r, 1500))")
        return self.eval("document.title")

    def reload(self, wait=4):
        """强制刷新当前页面（SPA 页面导航不稳定时用）"""
        self.msg_id += 1
        mid = self.msg_id
        self.ws.send(json.dumps({
            "id": mid,
            "method": "Page.reload",
            "params": {"ignoreCache": True}
        }))
        deadline = time.time() + 10
        while time.time() < deadline:
            try:
                r = json.loads(self.ws.recv())
                if r.get("id") == mid:
                    break
            except Exception:
                break
        time.sleep(wait)
        self.eval("new Promise(r => setTimeout(r, 1500))")
        return self.eval("document.title")

    def wait_for_rows(self, timeout=15, min_rows=1):
        """等待 el-table 出现数据行（SPA 异步加载用）"""
        deadline = time.time() + timeout
        while time.time() < deadline:
            cnt = self.eval("document.querySelectorAll('.el-table__body-wrapper .el-table__row').length")
            try:
                if int(cnt) >= min_rows:
                    return int(cnt)
            except Exception:
                pass
            self.sleep(1)
        try:
            return int(cnt)
        except Exception:
            return 0

    def wait_for_selector(self, selector, timeout=15):
        """等待某选择器出现"""
        deadline = time.time() + timeout
        while time.time() < deadline:
            found = self.eval(f"!!document.querySelector('{selector}')")
            if found == True or str(found).lower() == "true":
                return True
            self.sleep(1)
        return False

    def clear_loading_masks(self):
        """清除页面上的 el-loading-mask 透明遮罩（会挡住点击）"""
        res = self.eval("""(() => {
            const masks = document.querySelectorAll('.el-loading-mask, .el-loading-mask[style]');
            let removed = 0;
            for(const m of masks) {
                const st = getComputedStyle(m);
                const isVisible = st.display !== 'none' && parseFloat(st.opacity || '1') > 0.1;
                if(isVisible) {
                    m.remove();
                    removed++;
                }
            }
            return 'REMOVED:' + removed;
        })()""")
        return res

    def click_safe(self, selector):
        """清除遮罩后点击元素（安全点击）"""
        self.clear_loading_masks()
        return self.click_el(selector)

    def sleep(self, seconds):
        time.sleep(seconds)

    # ---------- 页面元素操作 ----------

    def visible_buttons(self):
        """列出页面可见按钮"""
        return self.eval("""(() => {
            const btns = document.querySelectorAll('.el-button, button');
            return [...btns].filter(b => b.offsetParent !== null && b.textContent.trim())
                .map(b => '[' + b.textContent.trim().substring(0,20) + '] cls:' + b.className.toString().substring(0,50))
                .join('\\n');
        })()""")

    def click_button(self, text, partial=True):
        """点击文本匹配的按钮（部分匹配）"""
        return self.eval(f"""(() => {{
            const btns = document.querySelectorAll('.el-button, button');
            const mode = {'true' if partial else 'false'};
            const btn = [...btns].find(b => b.offsetParent !== null &&
                (mode ? b.textContent.includes('{text}') : b.textContent.trim() === '{text}'));
            if(!btn) return 'NOT_FOUND';
            btn.click();
            return 'CLICKED';
        }})()""")

    def click_el(self, selector):
        """点击指定 CSS 选择器元素"""
        return self.eval(f"""(() => {{
            const el = document.querySelector('{selector}');
            if(!el) return 'NOT_FOUND';
            el.click();
            return 'CLICKED';
        }})()""")

    def read_inputs(self):
        """读取页面所有可见输入框的值"""
        return self.eval("""(() => {
            const inputs = document.querySelectorAll('.el-input__inner, input[type=text], input:not([type])');
            return [...inputs].filter(i => i.offsetParent !== null)
                .map((i, idx) => idx + ':[' + (i.placeholder || '') + ']=' + i.value).join('\\n');
        })()""")

    def set_input(self, selector, value):
        """设置输入框值（Element UI React/Vue 受控组件）"""
        # 用 JSON 安全转义
        v = json.dumps(str(value), ensure_ascii=False)
        return self.eval(f"""(() => {{
            const el = document.querySelector('{selector}');
            if(!el) return 'NOT_FOUND';
            el.focus();
            const proto = el.tagName === 'TEXTAREA' ? HTMLTextAreaElement.prototype
                : el.tagName === 'SELECT' ? HTMLSelectElement.prototype
                : HTMLInputElement.prototype;
            const setter = Object.getOwnPropertyDescriptor(proto, 'value').set;
            setter.call(el, {v});
            el.dispatchEvent(new Event('input', {{bubbles: true}}));
            el.dispatchEvent(new Event('change', {{bubbles: true}}));
            return 'SET_OK';
        }})()""")

    def get_visible_dialogs(self):
        """列出所有可见弹窗的标题和表单（检查外层 wrapper 的 display）"""
        return self.eval("""(() => {
            const ds = document.querySelectorAll('.el-dialog');
            const out = [];
            for(const d of ds) {
                // 检查自身及外层 wrapper 是否真正可见
                let isVis = false;
                let node = d;
                for(let i=0; i<3 && node; i++) {
                    const st = getComputedStyle(node);
                    if(st.display !== 'none' && st.visibility !== 'hidden' && parseFloat(st.opacity || '1') > 0.1) {
                        isVis = true;
                        node = node.parentElement;
                    } else {
                        isVis = false;
                        break;
                    }
                }
                if(isVis) {
                    const title = d.querySelector('.el-dialog__title');
                    const labels = [...d.querySelectorAll('.el-form-item__label')].map(l => l.textContent.trim());
                    const hasBody = !!d.querySelector('.el-dialog__body') && d.querySelector('.el-dialog__body').innerHTML.trim().length > 0;
                    out.push('TITLE:[' + (title ? title.textContent.trim() : '无') + '] HAS_BODY:' + hasBody + ' LABELS:[' + labels.join('|') + ']');
                }
            }
            return out.length ? out.join('\\n') : 'NO_VISIBLE_DIALOG';
        })()""")

    def dialog_click(self, btn_text):
        """在弹窗中点击指定按钮"""
        return self.eval(f"""(() => {{
            const btns = document.querySelectorAll('.el-dialog button, .el-dialog .el-button');
            const btn = [...btns].find(b => b.textContent.includes('{btn_text}'));
            if(!btn) return 'NOT_FOUND';
            btn.click();
            return 'CLICKED';
        }})()""")

    # ---------- 表格操作 ----------

    def read_table(self, max_rows=100):
        """读取 el-table 数据（每行返回单元格文本数组）"""
        res = self.eval(f"""(() => {{
            const rows = document.querySelectorAll('.el-table__body-wrapper .el-table__row');
            return JSON.stringify([...rows].slice(0, {max_rows}).map(row => {{
                const cells = row.querySelectorAll('td .cell');
                return [...cells].map(c => c.textContent.trim());
            }}));
        }})()""")
        try:
            return json.loads(res)
        except Exception:
            return [["PARSE_ERROR", res[:200]]]

    def read_table_with_switch_state(self, max_rows=100):
        """读取表格数据，附带每行开关状态"""
        res = self.eval(f"""(() => {{
            const rows = document.querySelectorAll('.el-table__body-wrapper .el-table__row');
            return JSON.stringify([...rows].slice(0, {max_rows}).map(row => {{
                const cells = row.querySelectorAll('td .cell');
                const sws = row.querySelectorAll('.el-switch');
                return {{
                    cols: [...cells].map(c => c.textContent.trim()),
                    switches: [...sws].map(s => s.classList.contains('is-checked'))
                }};
            }}));
        }})()""")
        try:
            return json.loads(res)
        except Exception:
            return []

    def check_row(self, row_index, checked=True):
        """勾选/取消指定行 checkbox"""
        flag = 'true' if checked else 'false'
        return self.eval(f"""(() => {{
            const rows = document.querySelectorAll('.el-table__body-wrapper .el-table__row');
            const row = rows[{row_index}];
            if(!row) return 'NO_ROW';
            const cb = row.querySelector('.el-checkbox');
            if(!cb) return 'NO_CHECKBOX';
            const isChecked = cb.classList.contains('is-checked');
            if({flag} !== isChecked) cb.click();
            return 'DONE';
        }})()""")

    def check_all(self, checked=True):
        """全选/取消全选"""
        flag = 'true' if checked else 'false'
        return self.eval(f"""(() => {{
            const cb = document.querySelector('.el-table__header-wrapper .el-checkbox');
            if(!cb) return 'NO_HEADER_CB';
            const isChecked = cb.classList.contains('is-checked');
            if({flag} !== isChecked) cb.click();
            return 'DONE';
        }})()""")

    def get_checked_count(self):
        """获取已勾选数量"""
        return self.eval("""(() => {
            const cb = document.querySelector('.el-table__header-wrapper .el-checkbox');
            if(!cb) return '-1';
            const cls = cb.className;
            const m = cls.match(/el-checkbox--(\\w+)/);
            if(!m) return '0';
            return m[1] === 'indeterminate' ? '>0' : (cls.includes('is-checked') ? 'ALL' : '0');
        })()""")

    def row_switch(self, row_index, switch_index, target_state=True):
        """切换指定行指定列的 el-switch
        switch_index: 0=自动发货, 1=售罄自动上架, 2=2人小刀
        """
        flag = 'true' if target_state else 'false'
        return self.eval(f"""(() => {{
            const rows = document.querySelectorAll('.el-table__body-wrapper .el-table__row');
            const row = rows[{row_index}];
            if(!row) return 'NO_ROW';
            const sws = row.querySelectorAll('.el-switch');
            const sw = sws[{switch_index}];
            if(!sw) return 'NO_SWITCH';
            const isOn = sw.classList.contains('is-checked');
            if({flag} !== isOn) {{
                // el-switch 点击 core 区域
                const core = sw.querySelector('.el-switch__core') || sw;
                core.click();
            }}
            return 'DONE';
        }})()""")

    def row_more_menu(self, row_index=0):
        """点击指定行的「更多」下拉，返回菜单项"""
        res = self.eval(f"""(() => {{
            const rows = document.querySelectorAll('.el-table__body-wrapper .el-table__row');
            const row = rows[{row_index}];
            if(!row) return 'NO_ROW';
            const link = row.querySelector('.el-dropdown-selfdefine');
            if(!link) return 'NO_DROPDOWN_LINK';
            // 触发 mouseenter 展开下拉
            const evts = ['mouseenter', 'mouseover'];
            for(const et of evts) {{
                try {{ link.dispatchEvent(new MouseEvent(et, {{bubbles: true}})); }} catch(e) {{}}
            }}
            return 'HOVERED';
        }})()""")
        time.sleep(1)
        # 读取展开的菜单
        menu = self.eval(f"""(() => {{
            const rows = document.querySelectorAll('.el-table__body-wrapper .el-table__row');
            const row = rows[{row_index}];
            const menus = row.querySelectorAll('.el-dropdown-menu');
            for(const m of menus) {{
                if(getComputedStyle(m).display !== 'none') {{
                    return [...m.querySelectorAll('.el-dropdown-menu__item')].map(i => i.textContent.trim()).join('|');
                }}
            }}
            return 'MENU_NOT_VISIBLE';
        }})()""")
        return menu

    # ---------- 状态与工具 ----------

    def get_url(self):
        return self.eval("location.href")

    def get_page_text(self, max_len=3000):
        """获取页面纯文本"""
        res = self.eval("document.body ? document.body.innerText : 'NO_BODY'")
        return res[:max_len] if isinstance(res, str) else str(res)[:max_len]

    def screenshot(self, filepath):
        """截图保存（可选实现，需要 Page.captureScreenshot）"""
        self.msg_id += 1
        mid = self.msg_id
        self.ws.send(json.dumps({
            "id": mid,
            "method": "Page.captureScreenshot",
            "params": {"format": "png"}
        }))
        while True:
            r = json.loads(self.ws.recv())
            if r.get("id") != mid:
                continue
            data = r.get("result", {}).get("data", "")
            if data:
                import base64
                with open(filepath, "wb") as f:
                    f.write(base64.b64decode(data))
                return f"SAVED:{filepath}"
            return "NO_DATA"

    # ---------- 文件上传（拦截文件选择框） ----------

    def _cmd(self, method, params=None, timeout=15):
        """通用 CDP 命令，返回 result dict"""
        self.msg_id += 1
        mid = self.msg_id
        self.ws.send(json.dumps({
            "id": mid, "method": method, "params": params or {}
        }))
        deadline = time.time() + timeout
        while time.time() < deadline:
            r = json.loads(self.ws.recv())
            if r.get("id") == mid:
                return r.get("result", {})
        return {}

    def upload_file(self, click_selector, filepath, timeout=15):
        """点击某个区域触发文件选择框并拦截，直接注入文件。
        适用于 el-upload / 自定义上传组件（如易店 .upLoad）。
        返回 'OK' 或错误信息。"""
        self.bring_to_front()
        # 1. 开启文件选择框拦截
        self._cmd("Page.enable")
        self._cmd("Page.setInterceptFileChooserDialog", {"enabled": True})
        # 2. 真实鼠标点击上传区域（JS 合成点击不触发原生文件选择框）
        pos = self.eval(f"""(() => {{
            const el = document.querySelector('{click_selector}');
            if(!el) return 'NOT_FOUND';
            el.scrollIntoView({{block:'center'}});
            const r = el.getBoundingClientRect();
            if(r.width === 0) return 'ZERO_SIZE';
            return JSON.stringify({{x: Math.round(r.left + r.width/2), y: Math.round(r.top + r.height/2)}});
        }})()""")
        try:
            c = json.loads(pos)
        except Exception:
            self._cmd("Page.setInterceptFileChooserDialog", {"enabled": False})
            return f"UPLOAD_AREA_NOT_FOUND:{pos}"
        self.mouse_click(c["x"], c["y"])
        # 3. 等 Page.fileChooserOpened 事件拿 backendNodeId
        backend_id = None
        deadline = time.time() + timeout
        self.ws.settimeout(2)
        try:
            while time.time() < deadline:
                try:
                    r = json.loads(self.ws.recv())
                except Exception:
                    continue
                if r.get("method") == "Page.fileChooserOpened":
                    backend_id = r.get("params", {}).get("backendNodeId")
                    break
        finally:
            self.ws.settimeout(20)
        if not backend_id:
            self._cmd("Page.setInterceptFileChooserDialog", {"enabled": False})
            return "NO_FILE_CHOOSER_EVENT"
        # 4. 注入文件
        self._cmd("DOM.setFileInputFiles", {
            "files": [os.path.abspath(filepath)],
            "backendNodeId": backend_id
        })
        # 5. 关闭拦截
        self._cmd("Page.setInterceptFileChooserDialog", {"enabled": False})
        time.sleep(2)  # 等上传请求发出
        return "OK"


if __name__ == "__main__":
    # 自测
    ed = EDClient()
    ed.connect()
    print("连接成功:", ed.target_url)
    print("页面标题:", ed.eval("document.title"))
    ed.close()
