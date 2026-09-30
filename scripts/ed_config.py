# -*- coding: utf-8 -*-
"""
ed_config.py - 鱼店配置自动化（自动发货/自动回复/免拼发货等开关管理）

页面：https://ed.weeeg.com/ekadmin/configuration/yudian_config/2/113
控件：el-radio-group（启用=value 1 / 关闭=value 0）
标签页：基础设置 | 消息设置 | 高级功能

用法：
    from ed_config import EDConfig
    cfg = EDConfig()
    cfg.read_all()                          # 读取全部开关状态
    cfg.set_auto_ship(True)                 # 开启自动发货
    cfg.set_by_label("自动回复", True)      # 按标签名设置开关
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp_tools import EDClient

CONFIG_URL = "https://ed.weeeg.com/ekadmin/configuration/yudian_config/2/113"


class EDConfig(EDClient):
    """鱼店配置自动化客户端"""

    def open_config_page(self):
        """打开鱼店配置页（强制刷新确保加载）"""
        try:
            url = self.get_url() or ""
            if "yudian_config" not in url:
                self.navigate(CONFIG_URL, wait=5)
            else:
                self.reload(wait=5)
        except Exception:
            self.navigate(CONFIG_URL, wait=5)
        # 移除遮挡的 loading mask
        self.eval("document.querySelectorAll('.el-loading-mask').forEach(m => m.remove())")
        self.sleep(1)
        return self.eval("document.title")

    def switch_tab(self, tab_text):
        """切换到指定标签页：基础设置/消息设置/高级功能"""
        res = self.eval(f"""(() => {{
            const tabs = document.querySelectorAll('.el-tabs__item, [role=tab]');
            const t = [...tabs].find(t => t.textContent.includes('{tab_text}') && t.offsetParent !== null);
            if(!t) return 'NOT_FOUND';
            if(!t.classList.contains('is-active')) t.click();
            return 'OK';
        }})()""")
        self.sleep(1.5)
        return res

    def _find_label_el(self, label_text):
        """在当前 tab 中找到指定标签的 radio 组，返回可执行脚本片段"""
        # 返回 (found, js) 或直接内联操作
        pass

    def read_current_tab(self):
        """读取当前标签页所有开关状态，返回 [{label, enabled}]"""
        res = self.eval("""(() => {
            const items = document.querySelectorAll('.el-form-item');
            const out = [];
            for(const it of items) {
                if(it.offsetParent === null) continue;
                const label = it.querySelector('.el-form-item__label');
                if(!label) continue;
                const radios = [...it.querySelectorAll('.el-radio')];
                // 排除只有"前往配置"链接的项（如自动评价）
                if(radios.length === 0) {
                    out.push({label: label.textContent.trim().replace(/[：:]/g,''), enabled: null, type:'link'});
                    continue;
                }
                const checkedRadio = radios.find(r => r.classList.contains('is-checked'));
                const enabled = checkedRadio ? checkedRadio.textContent.includes('启用') : null;
                out.push({label: label.textContent.trim().replace(/[：:]/g,''), enabled: enabled, type:'radio'});
            }
            return JSON.stringify(out);
        })()""")
        try:
            import json
            return json.loads(res)
        except Exception:
            return [{"error": res[:300]}]

    def read_all(self):
        """读取三个标签页的全部开关状态"""
        result = {}
        for tab in ["基础设置", "消息设置", "高级功能"]:
            self.switch_tab(tab)
            result[tab] = self.read_current_tab()
        return result

    def set_by_label(self, label_text, enabled, tab="基础设置"):
        """
        按标签名设置开关（用真实鼠标点击 radio 圆点，需页面在前台）
        label_text: 自动发货/自动回复/免拼发货/卡卷单发/异常通知/自动求花/...
        enabled: True=启用, False=关闭
        """
        self.open_config_page()
        self.switch_tab(tab)
        target_val = "1" if enabled else "0"
        # 1. 先看当前状态，若已是目标则直接返回
        current = self.read_current_tab()
        item = next((x for x in current if x.get("label") == label_text), None)
        if item is not None and item.get("enabled") == enabled:
            return f"ALREADY_{'ENABLED' if enabled else 'DISABLED'}"
        # 2. 获取目标 radio 圆点坐标
        res = self.eval(f"""(() => {{
            const items = document.querySelectorAll('.el-form-item');
            for(const it of items) {{
                if(it.offsetParent === null) continue;
                const label = it.querySelector('.el-form-item__label');
                if(!label) continue;
                const txt = label.textContent.trim().replace(/[：:]/g,'');
                if(txt !== '{label_text}') continue;
                const radio = [...it.querySelectorAll('.el-radio')]
                    .find(r => r.querySelector('input') && r.querySelector('input').value === '{target_val}');
                if(!radio) return 'NO_RADIO';
                const inner = radio.querySelector('.el-radio__inner') || radio;
                const r = inner.getBoundingClientRect();
                if(r.width === 0) return 'ZERO_SIZE';
                return JSON.stringify({{x: Math.round(r.left + r.width/2), y: Math.round(r.top + r.height/2)}});
            }}
            return 'LABEL_NOT_FOUND';
        }})()""")
        if not res or res.startswith("NO_") or res.startswith("LABEL_NOT_FOUND") or res.startswith("ZERO"):
            return f"FAILED: {res}"
        try:
            import json
            c = json.loads(res)
        except Exception:
            return f"PARSE_FAIL: {res}"
        # 3. 真实鼠标点击（自动 bringToFront）
        self.mouse_click(c["x"], c["y"])
        self.sleep(1.5)
        # 4. 验证
        verify = self.read_current_tab()
        vitem = next((x for x in verify if x.get("label") == label_text), None)
        if vitem and vitem.get("enabled") == enabled:
            return f"SET_OK_{'ENABLED' if enabled else 'DISABLED'}"
        return f"SET_FAILED: {vitem}"

    def set_auto_ship(self, enabled=True):
        """自动发货开关"""
        return self.set_by_label("自动发货", enabled)

    def set_auto_reply(self, enabled=True):
        """自动回复开关"""
        return self.set_by_label("自动回复", enabled)

    def set_mianpin(self, enabled=True):
        """免拼发货开关"""
        return self.set_by_label("免拼发货", enabled)

    def set_card_send(self, enabled=True):
        """卡卷单发开关"""
        return self.set_by_label("卡卷单发", enabled)

    def set_error_notify(self, enabled=True):
        """异常通知开关"""
        return self.set_by_label("异常通知", enabled)

    def set_auto_flower(self, enabled=True):
        """自动求花开关"""
        return self.set_by_label("自动求花", enabled)

    def save(self):
        """点击保存按钮"""
        res = self.eval("""(() => {
            const btns = document.querySelectorAll('button, .el-button');
            const save = [...btns].find(b => b.offsetParent !== null && b.textContent.trim() === '保存');
            if(!save) return 'NO_SAVE_BTN';
            save.click();
            return 'SAVED';
        })()""")
        self.sleep(2)
        return res

    def batch_configure(self, plan):
        """
        批量配置开关，一次性保存
        plan: {"基础设置": {"自动发货": True, "自动回复": False}, "消息设置": {...}}
        """
        self.open_config_page()
        changes = []
        for tab, items in plan.items():
            self.switch_tab(tab)
            for label, enabled in items.items():
                # 检查是否已是目标状态
                current = self.read_current_tab()
                item = next((x for x in current if x.get("label") == label), None)
                if item is None:
                    changes.append(f"{tab}/{label}: 未找到")
                    continue
                if item.get("enabled") == enabled:
                    changes.append(f"{tab}/{label}: 已是最新({enabled})")
                    continue
                r = self.set_by_label(label, enabled, tab=tab)
                if r == "SET_OK":
                    changes.append(f"{tab}/{label}: 设置成功 -> {'启用' if enabled else '关闭'}")
                else:
                    changes.append(f"{tab}/{label}: 设置失败({r})")
        self.save()
        return changes


if __name__ == "__main__":
    import json
    cfg = EDConfig()
    cfg.connect()
    print("=== 读取全部配置 ===")
    all_cfg = cfg.read_all()
    print(json.dumps(all_cfg, ensure_ascii=False, indent=2))
    cfg.close()
