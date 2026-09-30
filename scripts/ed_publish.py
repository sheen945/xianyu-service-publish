# -*- coding: utf-8 -*-
"""
ed_publish.py - 易店助手「添加商品」自动发布（模式K）
替代 goofish.com 网页直发：统一走 Chrome CDP（9222 端口），登录态只维护易店一处。
用法：
    from ed_publish import EDPublish
    pub = EDPublish()
    pub.connect()
    pub.publish({
        "title": "【宜昌】电商产品拍摄 ...",
        "desc": "完整描述（不含第一行标题）",
        "image": r"C:\\path\\card.png",
        "price": "68",
        "stock": "10",
        "category": "其他闲置",
        "city": ["湖北省", "宜昌市"],
        "shipping": "无需邮寄",
    }, dry_run=True)   # dry_run=True 只填表不点发布
    pub.close()
批量：
    python ed_publish_batch.py <数据文件> <主图目录> [起始序号] [只跑N个]
    数据文件格式与 publish-batch-node.js 相同：名称|图片|价1|价2|价3| + 描述块
"""
import os
import re
import sys
import time

from cdp_tools import EDClient

ADD_URL = "https://ed.weeeg.com/ekadmin/product/add_product"

# 中文文本统一走 unicode_escape 转义（fill_* 方法内实现），避免 eval 传参乱码


class EDPublish:
    def __init__(self):
        self.ed = EDClient()

    def connect(self):
        self.ed.connect()
        self.ed.bring_to_front()

    def close(self):
        self.ed.close()

    # ---------- 基础填表 ----------

    def _eval(self, code):
        return self.ed.eval(code)

    def open_add_page(self):
        self.ed.navigate(ADD_URL, wait=6)
        self.ed.clear_loading_masks()
        time.sleep(1)

    def fill_title(self, title):
        t = title.encode("unicode_escape").decode("ascii")
        return self._eval(f"""(()=>{{
            const inp=document.querySelector('input[placeholder*="宝贝标题"]');
            if(!inp) return 'NO_TITLE_INPUT';
            const set=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set;
            set.call(inp,'{t}');
            inp.dispatchEvent(new Event('input',{{bubbles:true}}));
            return 'OK:'+inp.value.length;
        }})()""")

    def fill_desc(self, desc):
        d = desc.encode("unicode_escape").decode("ascii")
        return self._eval(f"""(()=>{{
            const ta=document.querySelector('textarea[placeholder*="宝贝描述"]');
            if(!ta) return 'NO_DESC';
            const set=Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set;
            set.call(ta,'{d}');
            ta.dispatchEvent(new Event('input',{{bubbles:true}}));
            return 'OK:'+ta.value.length;
        }})()""")

    def fill_form_input_by_label(self, label_kw, value):
        """按表单项 label 找里面的 input 填值（售价/库存用）"""
        v = str(value).encode("unicode_escape").decode("ascii")
        lk = label_kw.encode("unicode_escape").decode("ascii")
        return self._eval(f"""(()=>{{
            const labs=[...document.querySelectorAll('label.el-form-item__label')];
            const lab=labs.find(l=>l.textContent.includes('{lk}'));
            if(!lab) return 'NO_LABEL';
            const item=lab.closest('.el-form-item');
            const inp=item.querySelector('input.el-input__inner, input[type=text], input:not([type])');
            if(!inp) return 'NO_INPUT';
            const set=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set;
            set.call(inp,'{v}');
            inp.dispatchEvent(new Event('input',{{bubbles:true}}));
            inp.dispatchEvent(new Event('change',{{bubbles:true}}));
            return 'OK:'+inp.value;
        }})()""")

    def pick_cascader_by_label(self, label_kw, path_texts):
        """级联选择：label_kw=商品分类/定位城市，path_texts=['其他闲置'] 或 ['湖北省','宜昌市']"""
        lk = label_kw.encode("unicode_escape").decode("ascii")
        r = self._eval(f"""(()=>{{
            const labs=[...document.querySelectorAll('label.el-form-item__label')];
            const lab=labs.find(l=>l.textContent.includes('{lk}'));
            if(!lab) return 'NO_LABEL';
            const item=lab.closest('.el-form-item');
            const inp=item.querySelector('.el-cascader input');
            if(!inp) return 'NO_CASCADER';
            inp.click();
            return 'OPENED';
        }})()""")
        if "OPENED" not in str(r):
            return r
        time.sleep(1.2)
        for txt in path_texts:
            t = txt.encode("unicode_escape").decode("ascii")
            rr = self._eval(f"""(()=>{{
                const menus=[...document.querySelectorAll('.el-cascader-menu')].filter(m=>m.offsetParent!==null);
                for(const m of menus){{
                    const n=[...m.querySelectorAll('.el-cascader-node')].find(x=>x.textContent.trim()==='{t}');
                    if(n && n.offsetParent!==null){{ n.click(); return 'PICKED'; }}
                }}
                return 'NOT_FOUND';
            }})()""")
            time.sleep(1.2)
            if "PICKED" not in str(rr):
                return f"FAIL_AT:{txt}"
        # 关闭面板
        self._eval("document.body.click()")
        return "OK"

    def pick_select_by_label(self, label_kw, option_text=None):
        """普通下拉选择：所属店铺。option_text=None 时选第一项"""
        lk = label_kw.encode("unicode_escape").decode("ascii")
        r = self._eval(f"""(()=>{{
            const labs=[...document.querySelectorAll('label.el-form-item__label')];
            const lab=labs.find(l=>l.textContent.includes('{lk}'));
            if(!lab) return 'NO_LABEL';
            const item=lab.closest('.el-form-item');
            const inp=item.querySelector('.el-select input');
            if(!inp) return 'NO_SELECT';
            inp.click();
            return 'OPENED';
        }})()""")
        if "OPENED" not in str(r):
            return r
        time.sleep(1.2)
        cond = "true" if option_text is None else f"i.textContent.includes('{option_text}')"
        rr = self._eval(f"""(()=>{{
            const dds=[...document.querySelectorAll('.el-select-dropdown')].filter(d=>d.offsetParent!==null);
            for(const d of dds){{
                const items=[...d.querySelectorAll('.el-select-dropdown__item')].filter(i=>i.offsetParent!==null);
                const t=items.find(i=>{cond});
                if(t){{ t.click(); return 'PICKED:'+t.textContent.trim(); }}
            }}
            return 'NOT_FOUND';
        }})()""")
        time.sleep(0.8)
        return rr

    def pick_radio_by_label(self, label_kw, option_text):
        """单选：运费设置 -> 无需邮寄"""
        lk = label_kw.encode("unicode_escape").decode("ascii")
        ot = option_text.encode("unicode_escape").decode("ascii")
        return self._eval(f"""(()=>{{
            const labs=[...document.querySelectorAll('label.el-form-item__label')];
            const lab=labs.find(l=>l.textContent.includes('{lk}'));
            if(!lab) return 'NO_LABEL';
            const item=lab.closest('.el-form-item');
            const radios=[...item.querySelectorAll('.el-radio, .el-radio-button')];
            const r=radios.find(x=>x.textContent.trim()==='{ot}');
            if(!r) return 'NO_RADIO:'+radios.map(x=>x.textContent.trim()).join('|');
            const inner=r.querySelector('.el-radio__inner, .el-radio-button__inner, input');
            (inner||r).click();
            r.click();
            return 'PICKED';
        }})()""")

    def upload_image(self, filepath):
        """上传宝贝图：真实鼠标点 .upLoad 打开「图片管理」弹窗
        → JS 点弹窗内「上传图片」（生成隐藏 input.el-upload__input）
        → DOM.requestNode + DOM.setFileInputFiles 注入文件
        → 等上传完成 → 点「使用选中图片」→ 点「确定」关弹窗"""
        import json as _json
        # 1. 真实鼠标点 .upLoad 打开图片管理弹窗（JS 点击打不开）
        pos = self.ed.eval("""(()=>{const el=document.querySelector('.upLoad');
            if(!el) return 'NOT_FOUND';
            el.scrollIntoView({block:'center'});
            const r=el.getBoundingClientRect();
            return JSON.stringify({x:Math.round(r.left+r.width/2),y:Math.round(r.top+r.height/2)})})()""")
        try:
            c = _json.loads(pos)
        except Exception:
            return f"UPLOAD_AREA_NOT_FOUND:{pos}"
        self.ed.mouse_click(c["x"], c["y"])
        time.sleep(2)
        # 2. JS 点「上传图片」按钮，让 el-upload 的隐藏 input 渲染出来
        r2 = self.ed.eval("""(()=>{
            const btns=[...document.querySelectorAll('.el-dialog button')];
            const b=btns.find(x=>x.offsetParent!==null && x.textContent.trim()==='上传图片');
            if(!b) return 'NO_UPLOAD_BTN';
            b.click();
            return 'CLICKED';
        })()""")
        if "CLICKED" not in str(r2):
            return str(r2)
        time.sleep(1.5)
        # 3. 抓隐藏 file input → 注入文件
        self.ed._cmd("DOM.enable")
        self.ed.msg_id += 1
        mid = self.ed.msg_id
        self.ed.ws.send(_json.dumps({
            "id": mid, "method": "Runtime.evaluate",
            "params": {"expression": "document.querySelector('input.el-upload__input')", "returnByValue": False}
        }))
        obj_id = None
        deadline = time.time() + 10
        while time.time() < deadline:
            r = _json.loads(self.ed.ws.recv())
            if r.get("id") == mid:
                obj_id = r.get("result", {}).get("result", {}).get("objectId")
                break
        if not obj_id:
            return "NO_FILE_INPUT_OBJ"
        rn = self.ed._cmd("DOM.requestNode", {"objectId": obj_id})
        node_id = rn.get("nodeId")
        self.ed._cmd("DOM.setFileInputFiles", {
            "files": [os.path.abspath(filepath)],
            "nodeId": node_id
        })
        time.sleep(4)  # 等图片上传完成
        # 4. 点「使用选中图片」→「确定」
        r4 = self.ed.eval("""(()=>{
            const btns=[...document.querySelectorAll('.el-dialog button')];
            const use=btns.find(b=>b.offsetParent!==null && b.textContent.includes('使用选中图片'));
            if(use){ use.click(); return 'USE_CLICKED'; }
            return 'NO_USE_BTN';
        })()""")
        time.sleep(1)
        r5 = self.ed.eval("""(()=>{
            const btns=[...document.querySelectorAll('.el-dialog button')];
            const ok=btns.find(b=>b.offsetParent!==null && (b.textContent.trim()==='确定' || b.textContent.trim()==='确 定'));
            if(ok){ ok.click(); return 'OK_CLICKED'; }
            return 'NO_OK_BTN';
        })()""")
        return f"OK use:{r4} ok:{r5}"

    def submit(self):
        """点发布按钮"""
        r = self._eval("""(()=>{
            const b=[...document.querySelectorAll('button')].find(x=>x.offsetParent!==null && x.textContent.trim()==='发布');
            if(!b) return 'NO_BTN';
            b.click();
            return 'CLICKED';
        })()""")
        return r

    def check_result(self, wait=6):
        """发布后的结果判定：成功提示 / 错误提示 / 跳转"""
        time.sleep(wait)
        return self._eval("""(()=>{
            const msgs=[...document.querySelectorAll('.el-message, .el-message-box')].map(m=>m.textContent.trim()).filter(Boolean);
            const errs=[...document.querySelectorAll('.el-form-item__error')].map(e=>e.textContent.trim()).filter(Boolean);
            return JSON.stringify({url:location.href, msgs, errs});
        })()""")

    # ---------- 完整发布 ----------

    def publish(self, item, dry_run=False):
        """item: dict(title, desc, image, price, stock, category, city, shipping)"""
        log = []
        self.open_add_page()

        log.append("title:" + str(self.fill_title(item["title"])))
        log.append("desc:" + str(self.fill_desc(item.get("desc", ""))))

        if item.get("image") and os.path.exists(item["image"]):
            log.append("img:" + str(self.upload_image(item["image"])))
            time.sleep(3)
        else:
            log.append("img:SKIP_NO_FILE")

        log.append("cat:" + str(self.pick_cascader_by_label("商品分类", [item.get("category", "其他闲置")])))
        log.append("city:" + str(self.pick_cascader_by_label("定位城市", item.get("city", ["湖北省", "宜昌市"]))))
        log.append("shop:" + str(self.pick_select_by_label("所属店铺")))
        log.append("price:" + str(self.fill_form_input_by_label("售价", item.get("price", "9.9"))))
        if item.get("stock"):
            log.append("stock:" + str(self.fill_form_input_by_label("库存", item["stock"])))
        log.append("ship:" + str(self.pick_radio_by_label("运费设置", item.get("shipping", "无需邮寄"))))

        if dry_run:
            log.append("DRY_RUN_DONE")
            return log

        log.append("submit:" + str(self.submit()))
        log.append("result:" + str(self.check_result()))
        return log


def parse_data_file(path):
    """解析与 publish-batch-node.js 相同的数据文件"""
    with open(path, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()
    meta_idx = [i for i, l in enumerate(lines) if re.match(r"^[a-z0-9-]+\|[a-z0-9.-]+\.png\|", l)]
    items = []
    for k, mi in enumerate(meta_idx):
        parts = lines[mi].split("|")
        end = meta_idx[k + 1] if k + 1 < len(meta_idx) else len(lines)
        desc_lines = [l for l in lines[mi + 1:end] if l.strip() and not l.strip().startswith("#")]
        full = "\n".join(desc_lines).strip()
        first_nl = full.find("\n")
        title = full[:first_nl] if first_nl > 0 else full
        desc = full[first_nl + 1:] if first_nl > 0 else ""
        items.append({
            "name": parts[0].strip(),
            "img": parts[1].strip(),
            "price": parts[2].strip() if len(parts) > 2 else "9.9",
            "title": title,
            "desc": desc,
        })
    return items


if __name__ == "__main__":
    print("ed_publish 模块：请用 ed_publish_batch.py 跑批量，或在代码里调用 EDPublish")
