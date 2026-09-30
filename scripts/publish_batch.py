# -*- coding: utf-8 -*-
"""
publish_batch.py — 闲鱼网页直发（goofish.com）批量发布驱动 v3.0

统一浏览器方案：Google Chrome + CDP 9222 + 固定登录态目录 chrome-cdp-profile
（见 `chrome-browser` 技能；不再依赖 QClaw 的 xb CLI）

替代：旧的 scripts/publish-batch-node.js（v2.0，走 node xb.cjs，已归档）

用法：
  python publish_batch.py --check                                  # 只做环境自检，不发布
  python publish_batch.py <数据文件> <主图目录> [起始序号0-based] [只跑N个]

数据文件格式（每商品）：
    名称|主图文件名|价格1|价格2|价格3|
    标题+描述（第一行即标题，可多行，空行分隔商品块）
日志输出：同目录 publish-batch-log.txt；失败截图：同目录 shots/
"""
import base64
import json
import os
import subprocess
import sys
import time

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp_tools import EDClient  # noqa: E402

# ===== 配置 =====
CDP = "http://127.0.0.1:9222"
PROFILE = r"C:\Users\Administrator\WorkBuddy\chrome-cdp-profile"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
GOOFISH_PATTERN = "goofish.com"
PUBLISH_URL = "https://www.goofish.com/publish"
ADDRESS = "民欣家园B区"      # 常用发货地址（发布弹窗选择）
WAIT_CLASSIFY = 6.0          # 图片识别等待（分类树切换为完整树）

_argv = sys.argv[1:]
CHECK_ONLY = bool(_argv) and _argv[0] == "--check"
DATA_FILE = None if CHECK_ONLY else (_argv[0] if _argv else None)
IMG_DIR = None if CHECK_ONLY else (_argv[1] if len(_argv) > 1 else None)
START_IDX = int(_argv[2]) if (not CHECK_ONLY and len(_argv) > 2) else 0
MAX_RUN = int(_argv[3]) if (not CHECK_ONLY and len(_argv) > 3) else 999
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(DATA_FILE)), "publish-batch-log.txt") if DATA_FILE else None
SHOT_DIR = os.path.join(os.path.dirname(os.path.abspath(DATA_FILE)), "shots") if DATA_FILE else None


# ===== 基础 =====
def cdp_alive():
    try:
        return requests.get(f"{CDP}/json/version", timeout=3).status_code == 200
    except Exception:
        return False


def ensure_goofish_tab():
    """确保有一个 goofish 标签页；没有就开一个（复用同一个 Chrome 实例）"""
    tabs = requests.get(f"{CDP}/json/list", timeout=5).json()
    if any(GOOFISH_PATTERN in t.get("url", "") for t in tabs):
        return
    try:
        requests.put(f"{CDP}/json/new?{PUBLISH_URL}", timeout=5)
    except Exception:
        pass
    for _ in range(12):
        time.sleep(1)
        tabs = requests.get(f"{CDP}/json/list", timeout=5).json()
        if any(GOOFISH_PATTERN in t.get("url", "") for t in tabs):
            return
    # 兜底：再向同一个 profile 发一次启动请求，Chrome 会在现有实例里开标签页
    subprocess.Popen([CHROME, "--remote-debugging-port=9222", f"--user-data-dir={PROFILE}", PUBLISH_URL])
    time.sleep(5)


def log(msg):
    line = "[%s] %s" % (time.strftime("%H:%M:%S"), msg)
    print(line)
    if LOG_FILE:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")


def sleep(sec):
    time.sleep(sec)


# ===== 数据解析 =====
def parse_data(content):
    """元数据行: 名称|图片.png|价1|价2|价3|"""
    lines = content.split("\n")
    meta_idx = [i for i, ln in enumerate(lines) if _is_meta(ln)]
    items = []
    for m, mi in enumerate(meta_idx):
        parts = lines[mi].strip().split("|")
        end = meta_idx[m + 1] if m + 1 < len(meta_idx) else len(lines)
        desc_lines = [l for l in lines[mi + 1:end] if l.strip() and not l.strip().startswith("#")]
        items.append({
            "name": parts[0].strip(),
            "img": parts[1].strip(),
            "p1": parts[2].strip(),
            "p2": parts[3].strip() if len(parts) > 3 else "",
            "p3": parts[4].strip() if len(parts) > 4 else "",
            "desc": "\n".join(desc_lines).strip(),
        })
    return items


def _is_meta(line):
    import re
    return bool(re.match(r"^[a-z0-9-]+\|[a-z0-9.-]+\.png\|", line))


# ===== JS 片段 =====
JS_INPUT_HACK = ("(()=>{const i=document.querySelector('input[type=file]');if(!i)return 'NO_INPUT';"
                 "i.style.cssText='display:block;position:fixed;top:10px;left:10px;zIndex:99999;"
                 "opacity:0.01;width:100px;height:30px';i.id='xianyu-upload';"
                 "i.setAttribute('aria-label','xianyu-upload-input');return 'OK'})()")

JS_OPEN_SELECT = ("(()=>{const sel=document.querySelector('.ant-select');if(!sel)return 'NO_SELECT';"
                  "const r=sel.getBoundingClientRect();const x=r.left+r.width/2,y=r.top+r.height/2;"
                  "const el=document.elementFromPoint(x,y);if(!el)return 'NO_EL';"
                  "const o={bubbles:true,cancelable:true,view:window,clientX:x,clientY:y,button:0};"
                  "['pointerdown','mousedown','pointerup','mouseup','click'].forEach(t=>{try{el.dispatchEvent(new MouseEvent(t,o))}catch(e){}});"
                  "return 'OPENED'})()")

JS_READ_OPTIONS = ("(()=>{const o=[...document.querySelectorAll('.ant-select-item-option')];"
                   "return o.map(x=>x.textContent.trim()).join('|')})()")

JS_PICK_OTHER = ("(()=>{const o=[...document.querySelectorAll('.ant-select-item-option')];"
                 "const t=o.find(x=>x.textContent.trim()==='其他闲置');if(!t)return 'NOT_FOUND';"
                 "t.click();return 'PICKED'})()")

JS_CLOSE_DROPDOWN = "(()=>{document.body.click();return 'closed'})()"

JS_READ_CAT = ("(()=>{const s=document.querySelector('.ant-select');if(!s)return 'NO_CAT';"
               "return 'CAT:'+s.textContent.trim().substring(0,40)})()")

JS_CLICK_PUBLISH = ("(()=>{const b=[...document.querySelectorAll('button')].find(b=>b.textContent.trim()==='发布');"
                    "if(!b)return 'NO_BTN';b.click();return 'CLICKED'})()")

JS_READ_ERR = ("(()=>{const e=document.querySelector('.ant-form-item-explain-error');"
               "return e?('ERR:'+e.textContent.trim()):'NO_ERR'})()")


def js_desc(desc_text):
    b64 = base64.b64encode(desc_text.encode("utf-8")).decode("ascii")
    return ("(()=>{const ed=document.querySelector('div[contenteditable=true]');if(!ed)return 'NO_EDITOR';"
            "ed.focus();const r=document.createRange();r.selectNodeContents(ed);"
            "const s=window.getSelection();s.removeAllRanges();s.addRange(r);"
            "document.execCommand('insertText',false,decodeURIComponent(escape(atob('" + b64 + "'))));"
            "return 'LEN:'+ed.textContent.length})()")


def js_price(p1, p2, p3):
    head = ("(()=>{const ins=[...document.querySelectorAll('input')].filter(i=>i.placeholder==='0.00');"
            "if(ins.length===0)return 'NO_PRICE';"
            "const set=(el,v)=>{const s=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set;"
            "s.call(el,String(v));el.dispatchEvent(new Event('input',{bubbles:true}));"
            "el.dispatchEvent(new Event('change',{bubbles:true}))};"
            "set(ins[0],'" + str(p1) + "');")
    mid = ("if(ins.length>1){set(ins[1],'" + str(p2) + "')};") if p2 else ""
    tail = ("if(ins.length>2){set(ins[2],'" + str(p3) + "')};") if p3 else ""
    return head + mid + tail + "return 'OK:'+ins.map(i=>i.value).join(',')})()"


def js_addr():
    return ("(()=>{const d=document.querySelector('[role=dialog]');if(!d||d.style.display==='none')return 'NO_DIALOG';"
            "const items=[...d.querySelectorAll('[class*=addressItem]')];if(items.length===0)return 'DIALOG_NO_ITEM';"
            "const t=items.find(i=>i.textContent.includes('" + ADDRESS + "'));if(t){t.click();return 'CLICKED_ADDR'}"
            "return 'ADDR_ITEMS:'+items.map(i=>i.textContent.trim().substring(0,20)).join('|')})()")


# ===== 发布单个商品 =====
def publish_item(ed, item, n, total):
    log("===== [%d/%d] %s 开始 =====" % (n, total, item["name"]))

    # 1. 打开发布页
    ed.navigate(PUBLISH_URL, wait=4)

    # 2. 改造隐藏 file input（上传区需要可见才能真实点击）
    r1 = ed.eval(JS_INPUT_HACK)
    if "NO_INPUT" in str(r1):
        log("❌ [%d] 无 file input: %s" % (n, r1))
        return False
    sleep(1)

    # 3. 上传主图（CDP 拦截文件选择框 + 注入文件）
    img_path = os.path.join(IMG_DIR, item["img"])
    if not os.path.exists(img_path):
        log("❌ [%d] 主图不存在: %s" % (n, img_path))
        return False
    up = ed.upload_file("#xianyu-upload", img_path, timeout=45)
    log("上传: %s" % ("OK" if up == "OK" else "FAIL " + str(up)[:120]))
    sleep(WAIT_CLASSIFY)          # 等图片识别完成（关键）

    # 4. 选分类：展开下拉选「其他闲置」
    cat_picked = False
    for try_cat in range(3):
        if cat_picked:
            break
        ed.eval(JS_OPEN_SELECT)
        sleep(1.2)
        opts = str(ed.eval(JS_READ_OPTIONS))
        if "其他闲置" in opts:
            picked = ed.eval(JS_PICK_OTHER)
            log("分类: 选中其他闲置 (%s)" % picked)
            cat_picked = True
        else:
            ed.eval(JS_CLOSE_DROPDOWN)
            log("分类: 第%d次展开无其他闲置 (%s), 重试中..." % (try_cat + 1, opts[:60]))
            sleep(2)
    if not cat_picked:
        log("⚠️ 未选到其他闲置, 当前分类: %s (可能不支持网页发布)" % ed.eval(JS_READ_CAT))
    sleep(1.5)

    # 5. 填描述
    desc_res = str(ed.eval(js_desc(item["desc"])))
    log("描述: %s" % desc_res)
    if "NO_EDITOR" in desc_res:
        log("❌ [%d] 无编辑器" % n)
        return False

    # 6. 填价格（React 受控组件原生 setter）
    log("价格: %s" % ed.eval(js_price(item["p1"], item["p2"], item["p3"])))

    # 7. 点发布 + 处理地址弹窗
    log("发布点击1: %s" % ed.eval(JS_CLICK_PUBLISH))
    sleep(3)
    addr_res = str(ed.eval(js_addr()))
    log("地址弹窗: %s" % addr_res)
    sleep(2)
    if "CLICKED_ADDR" in addr_res:
        log("发布点击2: %s" % ed.eval(JS_CLICK_PUBLISH))
        sleep(5)
    else:
        sleep(3)

    # 8. 验证结果
    url = str(ed.get_url())
    log("URL: %s" % url[:120])
    import re
    m = re.search(r"item\?id=(\d+)", url)
    if m:
        log("✅ [%d] %s 发布成功 id=%s" % (n, item["name"], m.group(1)))
        return True
    log("❌ [%d] %s 失败: %s" % (n, item["name"], ed.eval(JS_READ_ERR)))
    if SHOT_DIR:
        os.makedirs(SHOT_DIR, exist_ok=True)
        shot = os.path.join(SHOT_DIR, "fail-%02d.png" % n)
        try:
            ed.screenshot(shot)
            log("失败截图: %s" % shot)
        except Exception as exc:  # noqa: BLE001
            log("截图失败: %s" % exc)
    return False


def main():
    print("-" * 52)
    print("闲鱼网页直发批量驱动 v3.0（Chrome CDP 9222）")
    print("-" * 52)
    if not cdp_alive():
        print("❌ Chrome 调试端口 9222 未运行。")
        print("   由 AI 用危险模式豁免+Bash后台启动 Chrome（见 SKILL.md 沙盒限制段），不要让用户手动操作。")
        sys.exit(1)
    ver = requests.get(f"{CDP}/json/version", timeout=3).json().get("Browser", "?")
    print("[1] 浏览器: %s" % ver)
    ensure_goofish_tab()
    ed = EDClient()
    ed.connect(GOOFISH_PATTERN)
    print("[2] 已接管 goofish 标签页: %s" % str(ed.get_url())[:80])
    if CHECK_ONLY:
        print("[3] 环境自检通过（--check 模式，未执行发布）")
        ed.close()
        return
    if not DATA_FILE or not IMG_DIR:
        print("用法: python publish_batch.py <数据文件> <主图目录> [起始序号] [只跑N个]")
        print("      python publish_batch.py --check   # 只做环境自检")
        sys.exit(2)

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        items = parse_data(f.read())
    log("解析到 %d 个商品, 从 #%d 开始" % (len(items), START_IDX + 1))
    success, failed = 0, []
    end = min(len(items), START_IDX + MAX_RUN)
    for i in range(START_IDX, end):
        try:
            ok = publish_item(ed, items[i], i + 1, len(items))
        except Exception as exc:  # noqa: BLE001
            log("❌ [%d] 异常: %s" % (i + 1, exc))
            ok = False
        if ok:
            success += 1
        else:
            failed.append(items[i]["name"])
        sleep(2)
    log("========== 完成 ==========")
    log("成功: %d / %d" % (success, end - START_IDX))
    if failed:
        log("失败: %s" % ", ".join(failed))
    ed.close()


if __name__ == "__main__":
    main()
