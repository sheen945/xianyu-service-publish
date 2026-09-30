# -*- coding: utf-8 -*-
"""
ed_publish_batch.py - 易店助手批量发布新品（模式K 批量版）
用法: python ed_publish_batch.py <数据文件> <主图目录> [起始序号0-based] [只跑N个] [dry]
数据文件格式同旧版 publish-batch-node.js：名称|图片.png|价1|价2|价3| + 描述块
日志: 数据文件同目录 ed-publish-log.txt
"""
import os
import sys
import time

from ed_publish import EDPublish, parse_data_file

# 即梦主图生成（图片字段写 AUTO 时启用）
try:
    from gen_main_image import generate_main_images
    _HAS_JIMENG = True
except Exception:
    _HAS_JIMENG = False


def resolve_image(img_field, img_dir, item, log_path):
    """图片字段为 AUTO 时，调即梦现场生成主图（取候选第1张，候选2留底人工挑换）。"""
    field = str(img_field).strip()
    if not field.upper().startswith("AUTO"):
        return os.path.join(img_dir, img_field)
    if not _HAS_JIMENG:
        raise RuntimeError("图片字段为 AUTO 但 gen_main_image 模块不可用")
    # 支持 AUTO:drone 语法指定场景类型（photo/video/drone/repair/ai/design）
    svc_type = field.split(":", 1)[1].strip() if ":" in field else "default"
    log_line(log_path, f"[AUTO] 调即梦生成主图: {item['name']} (场景 {svc_type})")
    result = generate_main_images(item["name"], svc_type=svc_type,
                                  out_dir=img_dir, count=2)
    log_line(log_path, f"[AUTO] 模型 {result['model']} 出图 {len(result['images'])} 张")
    return result["images"][0]


def log_line(log_path, msg):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def main():
    if len(sys.argv) < 3:
        print("用法: python ed_publish_batch.py <数据文件> <主图目录> [起始序号] [只跑N个] [dry]")
        sys.exit(1)
    data_file = os.path.abspath(sys.argv[1])
    img_dir = os.path.abspath(sys.argv[2])
    start = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    max_run = int(sys.argv[4]) if len(sys.argv) > 4 else 999
    dry = len(sys.argv) > 5 and sys.argv[5] == "dry"
    log_path = os.path.join(os.path.dirname(data_file), "ed-publish-log.txt")

    items = parse_data_file(data_file)
    end = min(len(items), start + max_run)
    log_line(log_path, f"解析到 {len(items)} 个商品, 跑 #{start+1} ~ #{end}, dry={dry}")

    pub = EDPublish()
    pub.connect()

    ok, failed = 0, []
    for i in range(start, end):
        it = items[i]
        log_line(log_path, f"===== [{i+1}/{end}] {it['name']} 开始 =====")
        try:
            logs = pub.publish({
                "title": it["title"],
                "desc": it["desc"],
                "image": resolve_image(it["img"], img_dir, it, log_path),
                "price": it["price"],
                "category": "其他闲置",
                "city": ["湖北省", "宜昌市"],
                "shipping": "无需邮寄",
            }, dry_run=dry)
            joined = " | ".join(str(x) for x in logs)
            log_line(log_path, joined)
            # 成功判定：result 里 URL 离开 add_product 或 msgs 含成功
            if dry or ("result:" in joined and ("成功" in joined or "add_product" not in joined.split("result:")[-1])):
                ok += 1
                log_line(log_path, f"[{i+1}] {it['name']} 完成")
            else:
                failed.append(it["name"])
                log_line(log_path, f"[{i+1}] {it['name']} 疑似失败")
        except Exception as e:
            failed.append(it["name"])
            log_line(log_path, f"[{i+1}] {it['name']} 异常: {e}")
            try:
                pub.ed.reconnect()
            except Exception:
                pass
        time.sleep(4)  # 商品间隔防风控

    pub.close()
    log_line(log_path, f"========== 完成 ========== 成功 {ok}/{end-start}")
    if failed:
        log_line(log_path, "失败: " + ", ".join(failed))


if __name__ == "__main__":
    main()
