# xianyu-service-publish

A full-stack Xianyu (闲鱼) store-operations skill for WorkBuddy / CodeBuddy / Claude Code — it drives Chrome via the DevTools Protocol to automate the entire service-listing workflow: copywriting, main-image generation, form filling, publishing, product management, collection, card-key delivery, order statistics, and content-based traffic generation.

## Introduction

This repository is an AI skill for running a Xianyu store. The user scans a QR code to log in once; after that, the AI takes over daily operations: writing listings, generating main images, filling forms, publishing products, toggling switches, configuring smart replies, and compiling order statistics.

**What problems it solves:**
- Publishing service listings on Xianyu is tedious (title / description / images / category / price / stock, one by one), and batch listing is extremely time-consuming
- Operations are scattered across many modules of the Yidian (易店助手) admin console (products, config, replies, collection, cards, orders) with no unified automation entry point
- The platform enforces strict risk control — prohibited words or non-compliant categories can get all your listings taken down or your account banned, so the skill bakes compliance red lines into the AI's behavior

**Who it's for:**
- Individual sellers running service-category listings on Xianyu (photography/video, drones, AI services, local services, digital card-key goods, etc.)
- WorkBuddy / CodeBuddy / Claude Code users who want to run their store with natural language

**Key changes in v4.0:**
1. All publishing goes through Yidian (ed.weeeg.com, Mode K) — publishing via the goofish.com seller backend is forbidden
2. One browser only: Chrome with CDP port 9222 + a fixed profile directory `chrome-cdp-profile`; log in once and the session persists forever. Never switch browsers or profile directories
3. New environment self-check script `ensure_chrome.py` — always the first step of every task

**Trigger phrases (after installation, say any of these to activate the skill):** "在闲鱼发布XX服务", "批量发布", "帮我挂闲鱼", "易店商品管理", "开启自动发货", "配置智能回复", "小刀商品", "商品采集", "卡券管理".

## Features

**Main publish + management channel (Yidian ed.weeeg.com, Chrome CDP 9222):**

- **Mode K — Product publishing** (main channel): single-item (`ed_publish.py`) and batch (`ed_publish_batch.py`) publishing, with `dry_run` preview, resume-from-breakpoint, and anti-risk-control pacing
- **Mode E — Product management**: list/filter/search products; three per-row switches (auto-delivery / relist-when-sold-out / 2-person bargaining); batch switch operations; the per-row "More" menu (configure delivery / edit / duplicate / delist / delete)
- **Mode F — Store configuration**: global switches — auto-delivery, auto-reply, group-buy free shipping, card single-send, anomaly notifications, auto flower-requests; batch configuration saved in one shot
- **Mode G — Smart replies**: read, add, and toggle keyword / first-message / system-message reply rules to cut customer-service workload
- **Mode H — Product collection**: batch-collect products from other Xianyu stores into your own (publish immediately or save as drafts) — useful for scaling
- **Mode I — Card-key system**: card list / card-type management / batch import (text / file / system-generated) for automatic delivery of virtual goods
- **Mode J — Order statistics**: order list (9 status filters), status overview, sales stats (today / yesterday / day-over-day), review management

**Content traffic channel (Xianyu Creator Platform, author.goofish.com):**

- **Mode M — Creator posts**: guidelines and tactics for image-text posts (see `references/creator-platform.md`). Note: posts ≠ listings — no prices, promotions, contact info, or hard traffic redirection; grow via persona + value. Xianyu Circles can only be posted from the mobile app; the Creator Platform is the official desktop channel

**Diagnostics and fallback channels:**

- **Mode L — Search-visibility diagnosis** (read-only, zero risk-control exposure): search keywords as a buyer and check your products' ranking within the first 3 result pages to detect throttling (`check_visibility.py`)
- **Modes A/B/C — goofish.com direct publish** (v2.x legacy fallback): only when Yidian is unavailable and the user has confirmed; uses the same Chrome instance (port 9222 + same profile) — never launch a separate browser

**Supporting capabilities:**

- **Jimeng AI main-image generation** (`gen_main_image.py`): automatically picks the strongest image model via the New API gateway, ships a library of photo-realistic scene prompts (photo/video/drone/repair/ai/design), and auto-filters overseas AI tool names; in batch publishing, write `AUTO` in the image field to generate-then-publish
- **Code-drawn card images** (`make-service-card.ps1`): fallback when Jimeng is down; parameterized PowerShell rendering
- **Copywriting conversion rules + description template**: built-in rules for titles, body structure, scripts, and FAQs, plus a 33-service copywriting library (`references/service-library.md`)

## How It Works / Tech Stack

- **Browser automation**: Python 3 + Chrome DevTools Protocol (CDP over WebSocket, port 9222), depending on `requests` / `websocket-client`. All scripts go through the shared `cdp_tools.py` library to connect to Chrome, run JS eval, and simulate real mouse/keyboard events
- **Two-platform split**:
  - Publishing + management: Yidian admin `ed.weeeg.com/ekadmin` (Modes K/E/F/G/H/I/J)
  - Content traffic: Xianyu Creator Platform `author.goofish.com` (Mode M)
  - Fallback direct publish: `goofish.com` (Modes A/B/C only)
- **Form driving**: the Yidian backend is built on Element UI (el-radio-button / el-switch / el-dropdown, etc.); scripts use real mouse clicks, `Input.dispatchKeyEvent` for character-by-character input, and `execCommand('insertText')` for Chinese text injection
- **Persistent login state**: Yidian + Xianyu cookies all live in the fixed Chrome profile directory — log in once, stay logged in
- **AI image pipeline**: `gen_main_image.py` → New API gateway (127.0.0.1:3000) → Jimeng image models; the strongest available model is picked from `/v1/models` on every run

## Installation & Usage

### Installation

Copy this repository's contents into your skills directory, keeping the folder name `xianyu-service-publish`:

- WorkBuddy / CodeBuddy: `~/.workbuddy/skills/xianyu-service-publish/`
- Claude Code: `~/.claude/skills/xianyu-service-publish/`

Restart the session; the skill will then match automatically via the trigger phrases.

### Environment requirements (quick reference, unified since v4.0)

- Browser: Chrome (`C:\Program Files\Google\Chrome\Application\chrome.exe`) — no other browsers
- Chrome CDP port: 9222, launched with `--remote-debugging-port=9222 --remote-allow-origins=* --user-data-dir=C:\Users\Administrator\WorkBuddy\chrome-cdp-profile`
- Profile directory: `C:\Users\Administrator\WorkBuddy\chrome-cdp-profile` (Yidian + Xianyu cookies live here — do not delete or change)
- Self-check: `scripts/ensure_chrome.py` (first step of every task)
- Python: `C:\Users\Administrator\.workbuddy\binaries\python\envs\default\Scripts\python.exe` (deps: requests / websocket-client)
- Scripts directory: `C:\Users\Administrator\.workbuddy\skills\xianyu-service-publish\scripts\`

### Yidian module URLs

- Product management: `ed.weeeg.com/ekadmin/product/product_list`
- Add product (publish): `ed.weeeg.com/ekadmin/product/add_product`
- Store config: `ed.weeeg.com/ekadmin/configuration/yudian_config/2/113`
- Smart replies: `ed.weeeg.com/ekadmin/configuration/storereply`
- Product collection: `ed.weeeg.com/ekadmin/product/productcollect`
- Card management: `ed.weeeg.com/ekadmin/card/card_cdk`
- Order management: `ed.weeeg.com/ekadmin/order/list`

---

## Skill Manual (SKILL.md body)

# Publishing Service Listings on Xianyu

Browser-automation-based Xianyu store operations. **All publishing goes through Yidian (ed.weeeg.com)** — the user scans the QR code to log in; the AI handles copy, images, forms, publishing, and management.

## 🔒 Environment Rules (v4.0 — read before every task; violations cause repeated logins / stray browsers)

1. **One browser only: Google Chrome** (`C:\Program Files\Google\Chrome\Application\chrome.exe`).
   No Edge, no QClaw xb CLI, no agent-browser / playwright-cli — no other browser or automation tool, period.
2. **One debug port: 9222**. Every operation (publish/manage/collect/orders) connects to this same Chrome instance.
3. **One profile directory**: `C:\Users\Administrator\WorkBuddy\chrome-cdp-profile`
   - All Yidian + Xianyu cookies live here — **log in once, valid forever**
   - Never change the directory, never delete it, never clear its cache
   - ⚠️ On 2026-09-13 we switched from Edge to Chrome; cookies don't carry over, so **one re-login via QR code is required**, then it's permanent
4. **First step of every task**: run the environment self-check (if 9222 is alive, reuse it — never restart):
```powershell
cd C:\Users\Administrator\.workbuddy\skills\xianyu-service-publish\scripts
C:\Users\Administrator\.workbuddy\binaries\python\envs\default\Scripts\python.exe ensure_chrome.py
```
5. **QR scanning is needed in exactly one case**: first-time use, or the platform force-logging you out. Once logged in, cookies persist — **connect directly next time; never ask the user to log in again**.
6. **Publishing = Yidian**. Publishing via the goofish.com seller backend is forbidden (that's the fallback channel, used only with user confirmation when Yidian is down).
7. The Chrome launch command is fixed (must include these three arguments even when handwritten):
```powershell
Start-Process "C:\Program Files\Google\Chrome\Application\chrome.exe" -ArgumentList "--remote-debugging-port=9222","--remote-allow-origins=*","--user-data-dir=C:\Users\Administrator\WorkBuddy\chrome-cdp-profile","https://ed.weeeg.com/ekadmin/index"
```

> **⚠️ Sandbox limitation (revised 2026-09-15, must-read)**: browsers launched inside the sandbox are reclaimed when the command ends, and fail silently without an exemption.
> **Explicit user requirement (2026-09-15): the AI always launches the browser itself; never ask the user to do it manually.**
> The only approach verified to work (2026-09-15): launch in the foreground with **sandbox exemption (dangerouslyDisableSandbox=true) + run_in_background=true**, kept alive by the background task:
> ```bash
> exec "/c/Program Files/Google/Chrome/Application/chrome.exe" --remote-debugging-port=9222 --remote-allow-origins=* --user-data-dir="C:\\Users\\Administrator\\WorkBuddy\\chrome-cdp-profile" "https://ed.weeeg.com"
> ```
> ❌ Approaches verified NOT to work: `& disown`, cmd start, Python DETACHED_PROCESS/CREATE_BREAKAWAY_FROM_JOB — all get reclaimed when the command ends.
> Note: **PowerShell stdout capture is unreliable in this environment** (empty output ≠ failure); after launching, always verify the port is alive with Bash curl.
> Only involve the user for steps that genuinely require a human, like QR-code login; the desktop shortcut 「启动浏览器.exe」 is backup only.

---

## 🚫 Compliance Red Lines (highest priority — violations cause takedowns / bans)

**Verified 2026-08: 49 of the user's live listings were taken down by the platform for violations, with a 7-day penalty. The following red lines are permanently in effect:**

1. **Not a single character of overseas AI tool names**: ChatGPT, Claude, Codex, Midjourney, etc. (nowhere in the title, description, or main images — triggers the "unregistered generative AI service" violation)
2. **🚫 Model-deployment / model-service listings are permanently banned**: anything like "模型部署", "模型服务", "AI本地部署", "AI服务器", "AI助手部署" — don't write a single character of "模型/部署/服务" in the description (risk control lumps even domestic LLM deployment into violations)
3. **🚫 Drone training / certification listings are permanently banned**: "培训", "考证", "CAAC", "AOPA", "包过", "保过" constitute improper vocational-qualification advertising. Allowed drone services: repair, aerial photography, formation shows, custom DIY (copy must not mention certification/licenses/licensed pilots)
4. **Phrases like "持证飞行" / "持CAAC执照" are risky**: even when the service itself is legal (e.g. scenic-area aerial filming), don't mention licenses in the description — use "专业飞手" / "多年飞行经验" instead
5. **🚫 The title must never contain "批量生产"** (user-emphasized 2026-09-17): none of those four characters, and no variants like "批量产" or "量产"; express scale with "可接多单" / "高效交付" instead
6. **🚫 AI-boosting / fake-engagement services are permanently banned** (violation verified 2026-09-17): the listing was flagged as "AI托管违禁风险" under the rule "非法服务、票证、违反公序良俗类 > 不当获取流量或人气" — no follower/listener/ranking/traffic boosting, no referral-promotion services, no post bumping/deletion, no vote manipulation; the description must not contain "托管", "代刷", "代涨粉", "刷流量", etc.
7. **🚫 Medical errand services are permanently banned** (violation verified 2026-09-19): the listing was flagged as "代挂号违禁风险" under the rule "非法服务、票证、违反公序良俗类 > 不适宜开展的代办类服务" — **never write the two characters "代挂"**, nor 代挂号/代预约/代排队/就诊代排队/产科建档 or any medical-errand wording; likewise banned: license-plate/driver's-license/entry-permit/business-license/certificate errands, subsidy applications, license-point deduction, ghostwriting Party/government documents. Medical-adjacent copy may only describe compliant services (e.g. accompany-care with extreme caution, never touching appointment queuing) — when in doubt, don't publish
8. **No emoji in descriptions** (✅ etc. trigger validation errors) — use 【】 and - instead
9. **Self-check every listing against these red lines before publishing**

**Per-listing category notes**: prefer the "其他闲置" category; if the system recognizes a more suitable category that supports web publishing (e.g. "DeepSeek服务", "AI数字人"), use it; after uploading images, wait ~6 seconds before expanding the category dropdown to see the full "其他闲置" category tree.

**Additional red lines for the Yidian channel (v3.0):**

7. **Card-key products must have a legal source** (card numbers/secrets in the card system need legitimate authorization; no pirated resources)
8. **Collected products must not infringe intellectual property** (mind this when using the collection module)
9. **Auto-reply content must not contain prohibited words** (self-check when configuring smart replies, same as red lines 1–3)
10. **Never expose Yidian account credentials** (no hardcoding in scripts — use config files)
11. **Anti-risk-control for batch operations**: ≥1.5s interval between consecutive switch toggles; run batch listing/delisting in small chunks

---

## Mode K: Publishing via Yidian (v4.0 main channel — all publishing goes here)

Publish by filling the form in the Yidian admin (ed.weeeg.com/ekadmin/product/add_product). **No Xianyu login required**, and published products automatically enter the Yidian management system (Mode E for auto-delivery switches, etc.).

### Step 1: Environment self-check (mandatory every time)
```powershell
cd C:\Users\Administrator\.workbuddy\skills\xianyu-service-publish\scripts
C:\Users\Administrator\.workbuddy\binaries\python\envs\default\Scripts\python.exe ensure_chrome.py
```
- Output "已在运行 -> 直接复用" means ready; if not running, Chrome is auto-launched with the fixed profile directory
- Only when the Yidian session has expired does the user need to scan the QR code (login persists once done — don't make the user log in repeatedly)

### Step 2: Main image (upgraded 2026-09-15: Jimeng AI direct generation is preferred)

**Preferred: Jimeng AI main image, `scripts/gen_main_image.py`** (requires the New API gateway at 127.0.0.1:3000 to be online; the Jimeng service auto-starts at boot)
- No hardcoded model: picks the strongest image model from the gateway's `/v1/models` on every run (pro first > higher version > lite last; on 2026-09-15 it selected jimeng-image-5.0-pro)
- In-image text is the service name only (≤8 characters; longer names fall back to text-free images); **never put prices in images** (price changes shouldn't require regenerating images)
- Photo-realistic scene prompt library matched by service type: photo/video/drone/repair/ai/design
- Prompts auto-filter overseas AI tool names (compliance red line, see above)
- Usage: `python gen_main_image.py --name "无人机航拍" --type drone --tags 4K,航拍 --out-dir <image dir>`
- **Batch integration**: write `AUTO` (or `AUTO:drone` to force a scene type) in the data file's image field; `ed_publish_batch.py` generates the image before publishing. Two candidates per product — use the first, keep the second as a spare
- **Quality check (the AI's job)**: visually inspect each generated image for typos/occlusion/garbled text; if both candidates are bad, regenerate once; if still bad, degrade to the code-drawn card so publishing never stalls

**Fallback: code-drawn card** (when Jimeng is down, or for low-effort batch listing) via `scripts/make-service-card.ps1` (parameter usage: `references/legacy-goofish-direct.md`, Mode A step 2).

### Step 3: Single-product publish (code)
```python
import sys; sys.path.insert(0, r"C:\Users\Administrator\.workbuddy\skills\xianyu-service-publish\scripts")
from ed_publish import EDPublish

pub = EDPublish()
pub.connect()
log = pub.publish({
    "title": "【宜昌】电商产品拍摄 主图/详情页/短视频",   # ≤30 chars, follow the red lines
    "desc": "Full description (excludes the first-line title; same red lines, no emoji)",
    "image": r"C:\path\card.png",
    "price": "68",
    "stock": "10",
    "category": "其他闲置",
    "city": ["湖北省", "宜昌市"],
    "shipping": "无需邮寄",
}, dry_run=True)   # ⚠️ Always dry_run=True the first time to preview the form; publish for real only after user confirmation
pub.close()
```

### Step 4: Batch publishing
```powershell
cd C:\Users\Administrator\.workbuddy\skills\xianyu-service-publish\scripts
C:\Users\Administrator\.workbuddy\binaries\python\envs\default\Scripts\python.exe ed_publish_batch.py <data file> <image dir> [start index] [only N items] [dry]
```
- Data-file format is the same as the legacy version: `名称|图片.png|价1|价2|价3|` + description block
- Log file: `ed-publish-log.txt` in the same directory
- Run one item with `dry` first to validate form filling, then run for real

### ⚠️ Hard-won lessons
- `dry_run=True` fills the form without clicking publish — **the first publish must always be a dry preview**
- Category: "其他闲置" (consistent with the compliance red lines)
- For the form's "所属店铺" dropdown, pick the first option (single store)
- After publishing, check `check_result()`: URL leaving add_product or a success toast = success
- Successfully published products immediately appear in the Mode E product list, where you can toggle auto-delivery right away

---

## Modes A/B/C: goofish.com fallback direct publishing (⚠️ only when Yidian is unavailable, with user confirmation)

Mode K (Yidian) is always the first choice. Fallback cheat sheet:
- **Mode A single publish**: web form at goofish.com/publish, same Chrome 9222 + same profile; the first line of the description is the title; eval strings containing Chinese must be base64-transferred
- **Mode B batch publish**: `scripts/publish_batch.py` (run `--check` self-check first); data-file format is shared with Yidian batch publishing
- **Mode C universal prompt**: for a friend's account — read `assets/universal-prompt.md`, replace the city, and deliver as a Tencent Docs document

Full JS form-filling sequences, category selection, address-dialog handling, etc. → read `references/legacy-goofish-direct.md` (only when needed)

## Mode E: Yidian product management (new in v3.0)

Drives the Yidian admin via CDP to manage published products (both goofish-direct and Yidian-published products are managed here in one place).

### Prerequisites
0. Run the self-check first: `python ensure_chrome.py` (see Environment Rules; reuse port 9222 if already running)
1. Launch Chrome in CDP mode and log into Yidian:
```powershell
Start-Process "C:\Program Files\Google\Chrome\Application\chrome.exe" -ArgumentList "--remote-debugging-port=9222","--remote-allow-origins=*","--user-data-dir=C:\Users\Administrator\WorkBuddy\chrome-cdp-profile","https://ed.weeeg.com/ekadmin/index"
```
2. The user scans the QR code to log into the Yidian admin

### Running the script
```powershell
cd C:\Users\Administrator\.workbuddy\skills\xianyu-service-publish\scripts
C:\Users\Administrator\.workbuddy\binaries\python\envs\default\Scripts\python.exe ed_product.py
```

### Common operations
```python
from ed_product import EDProduct
p = EDProduct()
p.connect()

# 1. Read the on-sale product list (with switch states)
products = p.list_products(status="出售中", max_rows=50)
# Returns [{idx,id,shop,title,price,exposure,views,wants,auto_ship,resell,bargain,published,updated}]

# 2. Filter by status: 出售中/已下架/已售罄/已配置发货/未配置发货/定时上架
p.list_products(status="已下架")

# 3. Search by keyword
p.search_product("拍摄")

# 4. Switch overview stats
overview = p.view_switch_overview()  # counts of auto-delivery / relist / bargaining switches enabled

# 5. Set a row switch (⚠️ real change — requires user confirmation)
p.set_row_switch(0, "auto_ship", True)   # enable auto-delivery on row 0
p.set_row_switch(1, "resell", True)      # enable relist-when-sold-out on row 1
p.set_row_switch(2, "bargain", True)     # enable 2-person bargaining on row 2

# 6. Batch switch setting (⚠️ real change — requires user confirmation)
p.batch_set_switches(rows=[0,1,2], auto_ship=True, resell=True, bargain=True)

# 7. Per-row "More" menu (real mouse hover triggers the el-dropdown)
menu_items = p.row_more(0)               # returns: 配置发货 | 编辑商品 | 复制商品 | 下架宝贝 | 删除商品
p.row_more(0, "配置发货")                  # clicks the configure-delivery item (opens the dialog)

# 8. Open a row's "configure delivery" dialog (via the row's auto-delivery switch)
p.open_config_ship_dialog(0)              # dialog LABELS: 发货类型|商品规格|发货方式|网盘内容|消息模板|自动发货状态

# 9. Batch operations (⚠️ dry_run=True only checks boxes for preview — safe)
p.batch_action(rows=[0,1,2], action="上下架", dry_run=True)
```

### Per-row switch reference (3 switches)
| Index | Name | Effect |
|---|---|---|
| 0 | 自动发货 (auto-delivery) | Automatically sends delivery content after payment (delivery template must be configured first) |
| 1 | 售罄自动上架 (relist when sold out) | Automatically relists the product when it sells out |
| 2 | 2人小刀 (2-person bargaining) | Automatically accepts when two or more buyers bargain |

---

## Mode J: Order management & statistics (new in v3.0 P3)

View orders, manage reviews, and compile sales statistics.

### Running the script
```powershell
cd C:\Users\Administrator\.workbuddy\skills\xianyu-service-publish\scripts
C:\Users\Administrator\.workbuddy\binaries\python\envs\default\Scripts\python.exe ed_order.py
```

### Common operations
```python
from ed_order import EDOrder
o = EDOrder()
o.connect()

# 1. Read the order list
orders = o.list_orders(status="全部")
# status: 全部/待付款/待发货/待收货/退款中/交易完成/交易关闭/黑名单/待评价
# Returns [{idx, shop, order_id, product, user, amount, qty, status, pay_time, remark}]

# 2. Switch order status tab
o.switch_order_status("待发货")

# 3. Order status overview (counts of pending orders per state)
summary = o.get_order_summary()

# 4. Sales statistics
stats = o.get_sales_stats()  # orders/amount/refunds/buyers + today/yesterday/day-over-day

# 5. Go to review management
o.goto_evaluation()

# 6. Product-statistics tab
o.open_stat_page(tab="商品统计")

o.close()
```

### Statistics-card reference
| Metric | Contents |
|---|---|
| 销售订单(笔) | Today / yesterday / day-over-day / total completed orders |
| 销售金额(元) | Today / yesterday / day-over-day / total sales |
| 退款金额(元) | Today / yesterday / day-over-day / this month's refunds |
| 购买用户 | Today / yesterday / day-over-day / total buyers |
| 状态角标 | 待付款/待发货/待收货/退款中 |
| 图表 | Business trend / order-source analysis / order-type analysis |

---

## Mode H: Product collection (new in v3.0 P2)

Collect products from other Xianyu stores (or official sources) into your own store — good for scaling.

### Running the script
```powershell
cd C:\Users\Administrator\.workbuddy\skills\xianyu-service-publish\scripts
C:\Users\Administrator\.workbuddy\binaries\python\envs\default\Scripts\python.exe ed_collect.py
```

### Common operations
```python
from ed_collect import EDCollect
c = EDCollect()
c.connect()

# 1. Search products by keyword
results = c.search(keyword="拍摄", qtype="店铺商品")
# Returns [{idx, shop, product_id, title, price, published}]

# 2. Batch collect by ID (core feature: read the ID list from 总商品.txt)
ids = ["1077487223816", "1079912988993"]
c.collect_by_ids(ids, publish_mode="存草稿", dry_run=True)
# publish_mode: 立即发布 / 存草稿

# 3. Add a single row to the collection list
c.add_single_to_list(row_idx=0)

# 4. Batch add to the collection list (check rows first)
c.select_result_row(0, checked=True)
c.batch_add_to_list()

# 5. Go to the collection log to check progress
c.goto_log()

# 6. Go to drafts to see collected products pending publish
c.goto_draft()

c.close()
```

### Batch-collection configuration
- **商品ID列表**: textarea (comma/space/newline separated)
- **采集平台**: Xianyu
- **同步发货**: checkbox (auto-configure delivery for newly published products)
- **鱼小铺**: checkbox
- **自定义配置**: default config / custom config (category/city/stock/price/cost editable)
- **发布店铺**: select
- **发布方式**: publish immediately / save as draft

### ⚠️ Hard-won lessons
- dry_run=True fills the form without clicking "开始采集" — safe preview
- A "发布店铺" must be selected before real collection
- Yidian can only collect from Xianyu (not Taobao/other platforms)
- Product IDs must be Xianyu product IDs (not Taobao/Pinduoduo IDs)

---

## Mode I: Card-key system (new in v3.0 P2)

Manages cards (card numbers/secrets for virtual goods / cloud-drive resources).

### Running the script
```powershell
cd C:\Users\Administrator\.workbuddy\skills\xianyu-service-publish\scripts
C:\Users\Administrator\.workbuddy\binaries\python\envs\default\Scripts\python.exe ed_card.py
```

### Common operations
```python
from ed_card import EDCard
card = EDCard()
card.connect()

# 1. Read the card list
cards = card.list_cards(status="全部")
# status: 全部/未使用/已使用/使用中
# Returns [{idx, id, name, kind, no, secret(masked), status, order_id, used_by, used_at, created_at}]

# 2. Open the add-card dialog (auto-skips email binding)
dlg = card.open_add_card()

# 3. Fill the card-type name (step one)
card.fill_card_kind_name("试用资料包", dry_run=True)
card.close_add_card_dialog()

# 4. Switch to card-type management
card.switch_to_kind_manage()

card.close()
```

### Two-step add-card flow
1. **Step one**: enter the card-type name (auto-detects new vs. existing)
2. **Step two**: choose the fill method (text import / file import / system-generated)
   - Text import: paste card number + secret (one per line, space/tab separated)
   - File import: upload CSV/Excel
   - System-generated: auto-generate card numbers and secrets
3. Click "确定" to finish

### ⚠️ Hard-won lessons
- Write operations trigger a "绑定邮箱" dialog first — the script skips it
- Card list has 11 fields: ID/name/type/number/secret/status/purchase-order-ID/user/used-at/created-at/actions
- State machine: 全部→未使用→已使用→使用中

---

## Mode G: Smart-reply configuration (new in v3.0 P1)

Drives Yidian via CDP to manage smart-reply rules, cutting customer-service workload.

### Running the script
```powershell
cd C:\Users\Administrator\.workbuddy\skills\xianyu-service-publish\scripts
C:\Users\Administrator\.workbuddy\binaries\python\envs\default\Scripts\python.exe ed_reply.py
```

### Common operations
```python
from ed_reply import EDReply
r = EDReply()
r.connect()

# 1. Read all smart-reply rules
rules = r.list_rules()
# Returns [{idx, id, keyword, type, content_type, match_rule, products, shops, exclude, content, enabled}]

# 2. Add a keyword reply (dry_run=True fills without confirming; dry_run=False adds for real)
r.add_rule({
    "trigger_type": 0,      # 0 keyword reply / 1 first-message reply / 2 system message
    "match_type": 1,        # 0 no match / 1 contains / 2 equals
    "keywords": ["价格", "多少钱"],
    "content_type": 1,      # 1 text / 2 image / 3 text+image
    "reply_text": "您好，本店服务定价请看主页详情",
    "scope": 0,             # 0 global / 1 specific store/products
    "enabled": True
}, dry_run=True)

# 3. Toggle a rule's switch
r.toggle_rule(row_idx=0, enabled=False)

# 4. List smart-reply submenus (自动回复/AI智能回复/回复配置/模板管理/黑名单/图片管理)
r.list_reply_submenu()

r.close()
```

### Add-reply dialog fields
| Field | Widget | Values |
|---|---|---|
| 触发方式 | radio-button | 0 keyword reply / 1 first-message reply / 2 system message |
| 触发规则 | radio-button | 0 no match / 1 contains / 2 equals |
| 关键词 | tag-input | press Enter to add, max 20 |
| 内容类型 | radio-button | 1 text / 2 image / 3 text+image |
| 回复文本 | textarea | 25/500 chars |
| 适用范围 | radio-button | 0 global / 1 specific store/products |
| 排除商品 | button | click "+ 添加排除商品" |
| 开启状态 | switch | on by default |

### ⚠️ Hard-won lessons
- All controls in the add-reply dialog are el-radio-button (button-style radios) — switch them with real mouse clicks
- Keywords are typed with real keyboard Input.dispatchKeyEvent, character by character, + Enter
- Reply text is injected via execCommand('insertText', false, text) (supports Chinese)
- The free tier may restrict smart-reply features (the auto-reply switch is rejected by the backend)

---

## Mode F: Store configuration management (new in v3.0)

Manages Yidian's global switches (auto-delivery / auto-reply / group-buy free shipping, etc.).

### Running the script
```powershell
cd C:\Users\Administrator\.workbuddy\skills\xianyu-service-publish\scripts
C:\Users\Administrator\.workbuddy\binaries\python\envs\default\Scripts\python.exe ed_config.py
```

### Common operations
```python
from ed_config import EDConfig
cfg = EDConfig()
cfg.connect()

# 1. Read all config (three tabs: 基础设置/消息设置/高级功能)
all_cfg = cfg.read_all()

# 2. Set individual switches (⚠️ real change — requires user confirmation)
cfg.set_auto_ship(True)        # auto-delivery: enable
cfg.set_auto_reply(True)       # auto-reply: enable
cfg.set_mianpin(True)          # group-buy free shipping: enable
cfg.set_card_send(True)        # card single-send: enable
cfg.set_error_notify(True)     # anomaly notification: enable
cfg.set_auto_flower(False)     # auto flower-request: disable
cfg.save()                     # must click Save for changes to take effect!

# 3. Batch configuration (saved in one shot)
plan = {
    "基础设置": {"自动发货": True, "自动回复": True, "免拼发货": True},
    "消息设置": {"订单发货后发给买家": True},
}
changes = cfg.batch_configure(plan)
```

### Configuration reference
| Tab | Option | Notes |
|---|---|---|
| 基础设置 | 自动发货 | Auto-deliver after payment (**core** — products must have delivery content configured) |
| 基础设置 | 自动回复 | Auto-reply to buyer messages (use with Mode G reply rules) |
| 基础设置 | 免拼发货 | Auto ship group-buys without waiting (free tier ships without updating group status) |
| 基础设置 | 卡卷单发 | Send the card again separately after delivery |
| 基础设置 | 异常通知 | Email notification on non-delivery / status anomalies |
| 基础设置 | 自动评价 | Jump to review configuration |
| 基础设置 | 自动求花 | Automatically ask buyers for flowers after delivery |
| 消息设置 | 订单发货/收货/退款中 | Per-state buyer-notification switches |
| 高级功能 | 发货声明 | Statement attached to deliveries |

### ⚠️ Key lessons (verified 2026-08)
- Switches are **el-radio-group** (enable = value 1 / disable = value 0), not el-switch
- Changes take effect **only after clicking the "保存" button**
- Auto-delivery and other switches **may reset to off after saving** — read back to confirm
- **Do not refresh the page** after configuring (refreshing resets switch states)

---

## Mode L: Search-visibility diagnosis (new in v4.2, read-only, zero risk-control exposure)

Use when you suspect throttling / no exposure: search keywords as a buyer and see where your products rank within the first 3 result pages.

```powershell
cd C:\Users\Administrator\.workbuddy\skills\xianyu-service-publish\scripts
C:\Users\Administrator\.workbuddy\binaries\python\envs\default\Scripts\python.exe check_visibility.py "关键词" --ids 商品ID1,商品ID2
```

- How it works: opens a goofish.com search page in the port-9222 Chrome, scroll-loads ~60 results, and matches your product IDs
- Verdict: top 20 = normal weight; 21–60 = low weight; not found = strong throttling signal (double-check by direct ID search — findable by ID but not by keyword = confirmed search demotion)
- Product IDs come from Mode E's `list_products()`
- ⚠️ Read-only (searching = normal browsing), but don't run it at high frequency — a few times a day is plenty
- Post-diagnosis attribution and fixes → read `references/xianyu-risk-and-reply.md`, section 3

---

## Copywriting conversion rules (mandatory before publishing; absorbed from @尚工在吗 xianyu-listing-pro in v4.1)

Xianyu conversion = "searchable title + trustworthy copy + responsive scripts". When writing titles/descriptions, always:

1. **Title**: ≤30 chars, main search keyword in the first 15; structure = core keyword + long-tail keyword + scenario keyword
2. **Body structure**: pain-point opener → solution → trust signals (cases/experience) → price anchor → call to action
3. **Scripts**: keep three auto-replies ready — "can it be cheaper / how is it delivered / is it genuine" (configure in Mode G)
4. **FAQ to block refunds**: pre-answer 3–5 common objections at the end of the description
5. **Three tones**: digital goods (emphasize instant auto-delivery) / new physical goods (emphasize guarantees) / second-hand goods (emphasize honest condition)
6. **Copy red lines**: no fabricated sales/reviews ("已售1000+" claims must use real numbers); no off-platform transaction steering; digital goods must be labeled "非实物"

> Deeper operations tactics (traffic mechanics / pricing ladders / diagnosis funnels / competitor analysis) → read `references/xianyu-ops-playbook.md` (optional side quest, from @Lenny xianyu-service-ops, MIT)
> Price/title edits, throttling diagnosis, bargaining replies → read `references/xianyu-risk-and-reply.md` (optional side quest, from the goofish-cli built-in skill, Apache 2.0)

## Description template (generic for services)

```
{服务名}，{地域说明}。{核心价值一句话}。

【我是谁】{背景一句话，让人信任}

【服务内容】
1. {服务项1}
2. {服务项2}
3. {服务项3}

【价格】
- {档位1}：{价}元（{说明}）
- {档位2}：{价}元（{说明}）
- {档位3}：面议（{说明}）

【服务方式】{上门/远程/线上}，{范围}
【承诺】{不满意退款/包教包会/XX小时交付}
```

## Pitfall checklist (Top 8 must-know; full list in references/pitfalls.md)

1. The "其他服务" category can't be published from the web → must pick "其他闲置"
2. PowerShell scripts containing Chinese must be UTF-8 with BOM, otherwise garbled text and crashes
3. No emoji in descriptions (validation errors) — use 【】 and - instead
4. The price input is a React controlled component → native setter + dispatch input/change
5. The page must be in the foreground (`bringToFront()`) — CDP mouse events on background tabs are dropped
6. Leftover el-loading-mask blocks all clicks → call `clear_loading_masks()` first
7. Run each CDP/browser command individually and check each return value — never chain with `&&` / `;`
8. Store-config changes require clicking "保存", no page refresh afterwards, and a second read to confirm

The other 21 pitfalls (uploads/dropdowns/radios/dialogs/API endpoints and other troubleshooting details) → `references/pitfalls.md`

## Project Structure

```
xianyu-service-publish/
├── SKILL.md                        # Skill definition (trigger phrases + full operations manual)
├── README.md                       # Chinese README
├── README_EN.md                    # This file
├── .env.example                    # Environment variable example
├── assets/
│   └── universal-prompt.md         # Universal publish-prompt template (for friends without Yidian, via goofish)
├── references/                     # Deep reference docs (read only when needed)
│   ├── service-library.md          # 33-service copywriting library (8 photo/video, 5 drone, 9 AI, 7 lifestyle, 3 seasonal, photo restoration — each with image params + price + full description)
│   ├── legacy-goofish-direct.md    # (externalized in v4.2) full goofish.com fallback flow: Mode A/B/C JS form sequences, category selection, address-dialog handling
│   ├── pitfalls.md                 # (externalized in v4.2) complete 29-item pitfall list (only Top 8 kept in the main file)
│   ├── xianyu-ops-playbook.md      # Operations playbook (traffic mechanics / keywords / pricing ladders / diagnosis funnels / competitor analysis; from @Lenny xianyu-service-ops, MIT)
│   ├── xianyu-risk-and-reply.md    # Risk-control & customer-service scripts (Xianyu score / traffic pools / price-title edits / bargaining ladders / persona tone; from goofish-cli built-in skill, Apache 2.0)
│   ├── creator-platform.md         # Xianyu Creator Platform handbook (author.goofish.com posting rules / persona / trends / content red lines; per official requirements as of 2026-09-20)
│   └── 已废弃-xb-commands.md       # (deprecated, v2.x xb CLI era reference — archive only)
└── scripts/                        # All automation scripts
    ├── ensure_chrome.py            # ⭐ Environment self-check (first step of every task: reuse/launch Chrome 9222, fixed profile dir)
    ├── ed_publish.py               # ⭐ Mode K Yidian single-product publish (form fill / image upload / publish / result check)
    ├── ed_publish_batch.py         # ⭐ Mode K Yidian batch publish (resume / logging / anti-risk-control pacing)
    ├── cdp_tools.py                # Shared Yidian CDP toolkit (connect / eval / navigate / tables / switches)
    ├── ed_product.py               # Mode E product management automation (list / filter / search / switches / batch ops)
    ├── ed_config.py                # Mode F store-config automation (auto-delivery / auto-reply / group-buy shipping switches)
    ├── ed_reply.py                 # Mode G smart-reply configuration (add / read / toggle rules)
    ├── ed_collect.py               # Mode H product collection automation (search / batch IDs / publish or draft)
    ├── ed_card.py                  # Mode I card-key system automation (card list / add secrets / type management)
    ├── ed_order.py                 # Mode J order statistics automation (order list / statuses / sales stats)
    ├── check_visibility.py         # Mode L search-visibility diagnosis (buyer-perspective keyword search, throttling verdict)
    ├── gen_main_image.py           # Jimeng AI main-image generation (auto-picks strongest model, scene library, AUTO batch integration)
    ├── make-service-card.ps1       # Service-card image generator (parameterized, UTF-8 BOM)
    ├── publish_batch.py            # (fallback) goofish direct batch driver (Chrome CDP 9222; run `--check` first)
    └── (the rest are troubleshooting probes: probe_*.py / fix_price.py / try_prices.py / verify_all.py, etc.)
```

## Notes & Caveats

- **Tightly bound to Windows + Chrome**: all paths, launch commands, and the profile directory are verified Windows-environment configurations; other platforms require your own adaptation
- **Python dependencies**: `requests`, `websocket-client`, using WorkBuddy's bundled Python environment (`C:\Users\Administrator\.workbuddy\binaries\python\envs\default\Scripts\python.exe`)
- **Jimeng AI main images depend on the New API gateway** (127.0.0.1:3000) being online; when unavailable, the pipeline degrades to code-drawn cards
- **Compliance red lines are hard constraints**: in 2026-08, violations got 49 live listings taken down plus a 7-day penalty — self-check every listing before publishing
- **User confirmation before any write operation**: switch changes, batch publishing, rule additions — always preview with `dry_run` first and get user confirmation
- **The free tier of Yidian may restrict some features** (e.g. the smart-reply auto switch is rejected by the backend)
- **The profile directory is sacred**: don't delete it, don't change it, don't clear its cache — otherwise a fresh QR-code login is required

## License

MIT License

## Author

sheen945
