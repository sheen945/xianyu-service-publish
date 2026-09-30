# -*- coding: utf-8 -*-
"""以完全分离的方式启动 Chrome CDP（脱离父进程，命令结束后不被回收）。
用法: python start_chrome_detached.py [port] [url]
"""
import subprocess
import sys
import time
import urllib.request

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PROFILE = r"C:\Users\Administrator\WorkBuddy\chrome-cdp-profile"

DETACHED_PROCESS = 0x00000008
CREATE_NEW_PROCESS_GROUP = 0x00000200
CREATE_BREAKAWAY_FROM_JOB = 0x01000000


def cdp_alive(port: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=3) as r:
            return r.status == 200
    except Exception:
        return False


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9222
    url = sys.argv[2] if len(sys.argv) > 2 else "https://ed.weeeg.com"

    if cdp_alive(port):
        print(f"OK 端口 {port} 已在运行，无需重启")
        return

    args = [
        CHROME,
        f"--remote-debugging-port={port}",
        "--remote-allow-origins=*",
        f"--user-data-dir={PROFILE}",
        url,
    ]
    flags = DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP | CREATE_BREAKAWAY_FROM_JOB
    subprocess.Popen(args, creationflags=flags, close_fds=True,
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    for _ in range(10):
        time.sleep(1)
        if cdp_alive(port):
            print(f"OK Chrome 已启动，端口 {port} 存活")
            return
    print(f"FAIL 端口 {port} 未起来，请检查 Chrome 路径或端口占用")


if __name__ == "__main__":
    main()
