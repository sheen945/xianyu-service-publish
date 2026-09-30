# -*- coding: utf-8 -*-
"""
ensure_chrome.py - 闲鱼技能环境自检（每次任务第一步跑这个）

铁律（所有模式通用）：
  1. 唯一浏览器：Google Chrome（禁止 Edge / QClaw xb / agent-browser / playwright-cli）
  2. 唯一调试端口：9222
  3. 唯一配置目录：C:\\Users\\Administrator\\WorkBuddy\\chrome-cdp-profile
     —— 易店助手 + 闲鱼的登录态（Cookie）全存在这个目录里，
        登录一次永久有效。禁止换目录、禁止删目录、禁止清缓存。
  4. 9222 已在运行就直接复用，不要重启 Chrome

沙盒限制（2026-09-13 实测）：
  AI 这边启动的浏览器会在命令结束时被系统回收；需要浏览器长时间挂着时，
  让用户双击桌面「启动浏览器.exe」（由资源管理器持有，不会被回收）。

用法：
  python ensure_chrome.py             # 检查 + 按需启动 Chrome，打印状态
  python ensure_chrome.py --open-ed   # 顺便打开易店后台首页
  python ensure_chrome.py --open-xianyu  # 顺便打开闲鱼网页版（仅备用通道用）
"""
import subprocess
import sys
import time

import requests

CDP = "http://127.0.0.1:9222"
PROFILE = r"C:\Users\Administrator\WorkBuddy\chrome-cdp-profile"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
ED_HOME = "https://ed.weeeg.com/ekadmin/index"
XIANYU_HOME = "https://www.goofish.com"

PRINT_SEP = "-" * 46

DETACHED_PROCESS = 0x00000008
CREATE_NEW_PROCESS_GROUP = 0x00000200


def cdp_alive():
    try:
        r = requests.get(f"{CDP}/json/version", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def start_chrome(open_url=None):
    """用固定的 profile 目录启动 Chrome CDP 实例（登录态持久化的关键）"""
    args = [
        CHROME,
        "--remote-debugging-port=9222",
        "--remote-allow-origins=*",
        f"--user-data-dir={PROFILE}",
        "--no-first-run",
        "--no-default-browser-check",
    ]
    if open_url:
        args.append(open_url)
    subprocess.Popen(
        args,
        creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
        close_fds=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def list_tabs():
    try:
        return requests.get(f"{CDP}/json/list", timeout=5).json()
    except Exception:
        return []


def main():
    open_url = None
    if "--open-ed" in sys.argv:
        open_url = ED_HOME
    elif "--open-xianyu" in sys.argv:
        open_url = XIANYU_HOME

    print(PRINT_SEP)
    print("闲鱼技能环境自检（Chrome CDP / 9222）")
    print(PRINT_SEP)

    if cdp_alive():
        print("[1] Chrome CDP 9222 : 已在运行 -> 直接复用，不重启")
    else:
        print("[1] Chrome CDP 9222 : 未运行 -> 用固定登录态目录启动 Chrome ...")
        start_chrome(open_url)
        ok = False
        for _ in range(15):
            time.sleep(2)
            if cdp_alive():
                ok = True
                break
        print("    启动结果:", "成功" if ok else "失败（请手动检查 Chrome 路径）")
        if not ok:
            sys.exit(1)

    ver = requests.get(f"{CDP}/json/version", timeout=3).json()
    print("[2] 浏览器版本    :", ver.get("Browser", "?"))

    tabs = list_tabs()
    ed_open = [t for t in tabs if "ed.weeeg.com" in t.get("url", "")]
    xy_open = [t for t in tabs if "goofish.com" in t.get("url", "")]
    print("[3] 易店助手标签页:", f"已打开 x{len(ed_open)}" if ed_open else "未打开")
    print("[4] 闲鱼标签页    :", f"已打开 x{len(xy_open)}" if xy_open else "未打开")

    print(PRINT_SEP)
    print("登录态目录（勿删/勿换，登录一次永久有效）:")
    print("  ", PROFILE)
    print("发布宝贝 -> 一律走易店助手（ed_publish.py），禁止登闲鱼后台发布")
    print("浏览器未启动 -> AI 自己用危险模式豁免+Bash后台启动（见 SKILL.md），禁止让用户手动操作")
    print(PRINT_SEP)

    # 如果指定了 --open-* 但对应标签页没开，导航/打开
    if open_url and cdp_alive():
        host = "ed.weeeg.com" if "weeeg" in open_url else "goofish.com"
        if not any(host in t.get("url", "") for t in list_tabs()):
            try:
                requests.put(f"{CDP}/json/new?{open_url}", timeout=5)
                time.sleep(2)
            except Exception:
                start_chrome(open_url)
                time.sleep(3)
            print(f"已新开标签页: {open_url}")


if __name__ == "__main__":
    main()
