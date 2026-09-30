# -*- coding: utf-8 -*-
"""
gen_main_image.py - 闲鱼主图即梦生成模块（方案B：即梦直出整图）
特点：
  1. 模型不硬编码——每次从 New API 拉模型列表，自动选「最牛的一款」
     （pro 优先 > 版本号高优先 > lite 排最后）
  2. 图内文字压到最少：只放服务名（<=8字），不放价格（改价不用重出图）
  3. 实拍场景感提示词库，按服务类型自动匹配
  4. 每个商品出 2 张候选图，供质检挑选
  5. 提示词内置合规红线过滤

用法（命令行）:
  python gen_main_image.py --name "无人机航拍" --type drone --tags 4K,航拍 \
      --out-dir "C:/path/to/images" [--count 2]
输出：stdout 最后一行打印 JSON {"ok":true,"model":"...","images":["路径1","路径2"]}

也可被其他脚本 import：
  from gen_main_image import generate_main_images
  paths = generate_main_images("无人机航拍", svc_type="drone", out_dir="...")
"""
import argparse
import io
import json
import os
import re
import sys
import time
import urllib.request

# ---------- 链路配置（与 jimeng-generate 技能一致） ----------
API_BASE = "http://127.0.0.1:3000/v1"
API_KEY = os.environ.get("NEWAPI_TOKEN", "sk-YOUR_NEWAPI_TOKEN_HERE")
DEFAULT_OUT_DIR = r"C:\Users\Administrator\WorkBuddy\AI做视频相关\即梦生成\闲鱼主图"

# ---------- 合规红线：提示词里绝不允许出现的词 ----------
BANNED_WORDS = [
    "chatgpt", "openai", "claude", "gemini", "copilot", "midjourney",
    "stable diffusion", "sora", "runway", "pika", "kling", "dall-e",
    "grok", "deepseek", "anthropic", "google", "microsoft",
]

# ---------- 实拍场景库：按服务类型匹配 ----------
SCENES = {
    "photo": "专业摄影棚内景，摄影师手持相机正在拍摄，柔光箱灯光氛围，工作现场纪实感",
    "video": "短视频拍摄现场，稳定器和相机特写，监视器亮着，工作室纪实氛围",
    "drone": "户外开阔场地，无人机正在低空飞行，操作员手持遥控器，阳光自然，纪实风格",
    "repair": "维修工作台特写，工具整齐摆放，技师手部正在操作，暖色灯光，专业纪实感",
    "ai": "现代办公桌场景，显示器上有代码和图表氛围光，键盘特写，科技感工作室，纪实风格",
    "design": "设计师工作台，手绘板和显示器，屏幕上有设计稿氛围，明亮工作室，纪实风格",
    "default": "明亮整洁的工作台场景，专业设备特写，工作现场纪实感，自然光线",
}

# 服务名超过这个长度就拒绝写进图里（字越多越容易乱码）
MAX_TITLE_LEN = 8


def pick_best_model():
    """从 New API 拉模型列表，自动选最强的即梦生图模型。
    规则：jimeng-image-* 系列里，pro 后缀 +100 分，lite -50 分，版本号本身加权。
    """
    req = urllib.request.Request(
        API_BASE + "/models",
        headers={"Authorization": "Bearer " + API_KEY},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read().decode("utf-8"))
    candidates = []
    for m in data.get("data", []):
        mid = m.get("id", "")
        mm = re.match(r"^jimeng-image-(\d+)\.(\d+)(-(\w+))?$", mid)
        if not mm:
            continue
        score = int(mm.group(1)) * 10 + int(mm.group(2))
        suffix = mm.group(4) or ""
        if suffix == "pro":
            score += 100
        elif suffix == "lite":
            score -= 50
        candidates.append((score, mid))
    if not candidates:
        raise RuntimeError("模型列表里没找到 jimeng-image-* 模型，检查 New API 网关")
    candidates.sort(reverse=True)
    return candidates[0][1]


def sanitize_prompt(text):
    """合规红线过滤：剔除违禁词（不区分大小写）。"""
    cleaned = text
    for w in BANNED_WORDS:
        cleaned = re.sub(re.escape(w), "", cleaned, flags=re.IGNORECASE)
    return cleaned


def build_prompt(name, svc_type="default", tags=None):
    """拼提示词：实拍场景 + 图内只写服务名（<=8字），不放价格。"""
    scene = SCENES.get(svc_type, SCENES["default"])
    title_in_image = name if len(name) <= MAX_TITLE_LEN else None
    tag_str = "、".join(tags) if tags else ""
    prompt = (
        f"一张闲鱼服务主图，电商海报式构图，实拍照片质感。{scene}。"
    )
    if title_in_image:
        prompt += (
            f"图片上方有醒目的中文大字标题「{title_in_image}」，"
            "字体粗壮清晰、笔画正确无错字，标题排版美观。"
        )
    else:
        prompt += "图片上不要出现任何文字。"
    if tag_str:
        prompt += f"画面元素体现：{tag_str}。"
    prompt += "画面主体突出、色彩明快、高清商业摄影质感，不要水印。"
    return sanitize_prompt(prompt), title_in_image


def _post_json(url, payload, timeout=180):
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=body,
        headers={
            "Authorization": "Bearer " + API_KEY,
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _download(url, path):
    urllib.request.urlretrieve(url, path)


def generate_one(prompt, model, out_path):
    """调即梦出一张图并下载到本地。返回本地路径。"""
    resp = _post_json(API_BASE + "/images/generations", {
        "model": model,
        "prompt": prompt,
        "size": "1024x1024",
        "response_format": "url",
    })
    url = resp["data"][0]["url"]
    _download(url, out_path)  # 签名链接会过期，立刻下载
    return out_path


def generate_main_images(name, svc_type="default", tags=None, out_dir=DEFAULT_OUT_DIR,
                         count=2, model=None):
    """生成主图候选。返回 {"model":..., "images":[路径...]}。"""
    os.makedirs(out_dir, exist_ok=True)
    if not model:
        model = pick_best_model()
    prompt, _ = build_prompt(name, svc_type, tags)
    safe_name = re.sub(r'[\\/:*?"<>|\s]+', "_", name)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    images = []
    for i in range(count):
        out_path = os.path.join(out_dir, f"{safe_name}-{stamp}-{i+1}.png")
        generate_one(prompt, model, out_path)
        images.append(out_path)
    return {"model": model, "prompt": prompt, "images": images}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True, help="服务名（<=8字会写进图里）")
    ap.add_argument("--type", default="default",
                    help="服务类型: photo/video/drone/repair/ai/design/default")
    ap.add_argument("--tags", default="", help="卖点标签，逗号分隔")
    ap.add_argument("--out-dir", default=DEFAULT_OUT_DIR)
    ap.add_argument("--count", type=int, default=2)
    ap.add_argument("--model", default=None, help="手动指定模型（默认自动选最强）")
    args = ap.parse_args()

    tags = [t.strip() for t in args.tags.split(",") if t.strip()] or None
    try:
        result = generate_main_images(
            args.name, svc_type=args.type, tags=tags,
            out_dir=args.out_dir, count=args.count, model=args.model,
        )
        print(json.dumps({"ok": True, **result}, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    main()
