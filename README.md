# xianyu-service-publish

闲鱼全栈运营技能（WorkBuddy / CodeBuddy / Claude Code Skill）——通过 Chrome CDP 浏览器自动化，完成闲鱼服务类商品的发布、管理、采集、卡券、订单统计与内容引流全流程。

## 简介

这是一个面向闲鱼店铺运营的 AI 技能仓库。用户只需扫码登录一次，AI 即可接管文案撰写、主图生成、表单填写、商品发布、开关配置、智能回复、订单统计等全部日常运营动作。

**解决什么问题：**
- 闲鱼服务类商品发布流程繁琐（标题/描述/主图/分类/价格/库存逐项手工填写），批量铺货极其耗时
- 运营动作分散在易店助手后台的多个模块（商品、配置、回复、采集、卡券、订单），缺乏统一自动化入口
- 平台风控严格，违禁词、不合规类目会导致批量下架甚至封号，需要内建合规红线约束 AI 行为

**适合谁：**
- 在闲鱼经营服务类商品（拍摄剪辑、无人机、AI 服务、生活服务、资料卡券等）的个人卖家
- 使用 WorkBuddy / CodeBuddy / Claude Code，希望用自然语言驱动店铺运营的用户

**v4.0 核心修正：**
1. 发布宝贝一律走易店助手（ed.weeeg.com，模式 K），禁止登闲鱼后台（goofish.com）发布
2. 唯一浏览器 Chrome CDP 9222 + 固定登录态目录 `chrome-cdp-profile`，登录一次永久有效，禁止换浏览器/换目录
3. 新增环境自检脚本 `ensure_chrome.py`（每次任务第一步）

**触发场景（安装后说这些话即可自动匹配本技能）：**"在闲鱼发布XX服务"、"批量发布"、"帮我挂闲鱼"、"易店商品管理"、"开启自动发货"、"配置智能回复"、"小刀商品"、"商品采集"、"卡券管理"。

## 功能列表

**发布 + 管理主通道（易店助手 ed.weeeg.com，Chrome CDP 9222）：**

- **模式 K 发布商品** —— 主通道。单发（`ed_publish.py`）/ 批量（`ed_publish_batch.py`），支持 `dry_run` 预览、断点续跑、防风控间隔
- **模式 E 商品管理** —— 商品列表/筛选/搜索，行内三开关（自动发货/售罄上架/2人小刀），批量开关、行内「更多」菜单（配置发货/编辑/复制/下架/删除）
- **模式 F 鱼店配置** —— 全局开关管理：自动发货/自动回复/免拼发货/卡卷单发/异常通知/自动求花，支持批量配置一次性保存
- **模式 G 智能回复** —— 关键词/首次/系统消息回复规则的读取、添加、启停，降低客服成本
- **模式 H 商品采集** —— 从其他闲鱼店铺批量采集商品到自己店铺（立即发布或存草稿），适合扩规模
- **模式 I 卡券系统** —— 卡卷列表/卡种管理/批量导入（文本/文件/系统生成），用于虚拟商品自动发货
- **模式 J 订单统计** —— 订单列表（9 种状态筛选）、状态概览、销售统计（今日/昨日/环比）、评价管理

**内容引流通道（闲鱼创作者平台 author.goofish.com）：**

- **模式 M 创作者发帖** —— 图文帖子创作规范与引流打法（详见 `references/creator-platform.md`）。注意：帖子≠宝贝，禁价格/促销/联系方式/硬导流，靠人设+价值软引流；闲鱼圈子只能手机 App 发，创作者平台是电脑端发内容的官方通道

**诊断与备用通道：**

- **模式 L 搜索可见性诊断** —— 纯读取零风控。以买家视角搜关键词，看自家商品在前 3 页的排名，判定是否被限流（`check_visibility.py`）
- **模式 A/B/C goofish.com 备用直发**（v2.x 遗留）—— 仅易店助手不可用时，经用户确认后启用；同一 Chrome 实例（9222 + 同一 profile），不要另起浏览器

**辅助能力：**

- **即梦 AI 主图生成**（`gen_main_image.py`）—— 经 New API 网关自动选最强生图模型，实拍场景感提示词库（photo/video/drone/repair/ai/design），自动过滤境外 AI 工具名；批量发布时数据文件图片字段写 `AUTO` 即可先生图再发布
- **代码卡片主图**（`make-service-card.ps1`）—— 即梦服务不可用时的备选方案，PowerShell 参数化绘制
- **文案转化法则 + 服务文案模板** —— 内建标题/正文/话术/FAQ 写作规范，及 33 项服务完整文案库（`references/service-library.md`）

## 工作原理与技术栈

- **浏览器自动化**：Python 3 + Chrome DevTools Protocol（CDP，端口 9222，WebSocket），依赖 `requests` / `websocket-client`。所有脚本经 `cdp_tools.py` 通用工具库连接 Chrome、执行 JS eval、模拟真实鼠标/键盘事件
- **双平台分工**：
  - 发布 + 管理：易店助手 `ed.weeeg.com/ekadmin`（模式 K/E/F/G/H/I/J）
  - 内容引流：闲鱼创作者平台 `author.goofish.com`（模式 M）
  - 备用直发：`goofish.com`（仅模式 A/B/C）
- **表单驱动**：易店后台为 Element UI（el-radio-button / el-switch / el-dropdown 等），脚本用真实鼠标点击 + `Input.dispatchKeyEvent` 逐字符输入 + `execCommand('insertText')` 注入中文
- **登录态持久化**：易店 + 闲鱼 Cookie 全部存于固定 Chrome profile 目录，登录一次永久有效
- **AI 生图链路**：`gen_main_image.py` → New API 网关（127.0.0.1:3000）→ 即梦（Jimeng）生图模型，每次从 `/v1/models` 自动挑选最强可用模型

## 安装与使用

### 安装

把本仓库的目录内容复制到你的技能目录下，文件夹名保持 `xianyu-service-publish`：

- WorkBuddy / CodeBuddy：`~/.workbuddy/skills/xianyu-service-publish/`
- Claude Code：`~/.claude/skills/xianyu-service-publish/`

重启会话后即可通过触发词自动匹配。

### 环境要求（运行环境速查，v4.0 统一）

- 浏览器：Chrome（`C:\Program Files\Google\Chrome\Application\chrome.exe`），禁止其他浏览器
- Chrome CDP 端口：9222，启动参数 `--remote-debugging-port=9222 --remote-allow-origins=* --user-data-dir=C:\Users\Administrator\WorkBuddy\chrome-cdp-profile`
- 登录态目录：`C:\Users\Administrator\WorkBuddy\chrome-cdp-profile`（易店+闲鱼 Cookie 都在这，勿删勿换）
- 环境自检：`scripts/ensure_chrome.py`（每次任务第一步）
- Python：`C:\Users\Administrator\.workbuddy\binaries\python\envs\default\Scripts\python.exe`（依赖 requests/websocket-client）
- 脚本目录：`C:\Users\Administrator\.workbuddy\skills\xianyu-service-publish\scripts\`

### 易店模块 URL

- 商品管理：`ed.weeeg.com/ekadmin/product/product_list`
- 添加商品（发布）：`ed.weeeg.com/ekadmin/product/add_product`
- 鱼店配置：`ed.weeeg.com/ekadmin/configuration/yudian_config/2/113`
- 智能回复：`ed.weeeg.com/ekadmin/configuration/storereply`
- 商品采集：`ed.weeeg.com/ekadmin/product/productcollect`
- 卡卷管理：`ed.weeeg.com/ekadmin/card/card_cdk`
- 订单管理：`ed.weeeg.com/ekadmin/order/list`

---

## 技能说明（SKILL.md 正文）

# 闲鱼服务类商品发布

用浏览器自动化做闲鱼店铺运营。**发布宝贝一律走易店助手**（ed.weeeg.com），用户负责扫码登录，AI 负责文案、图片、填表、发布、管理。

## 🔒 环境铁律（v4.0，每次任务必读，违反会重复登录/乱开浏览器）

1. **唯一浏览器：Google Chrome**（`C:\Program Files\Google\Chrome\Application\chrome.exe`）。
   禁止 Edge、禁止 QClaw xb CLI、禁止 agent-browser / playwright-cli、禁止任何其他浏览器/自动化工具。
2. **唯一调试端口：9222**。所有操作（发布/管理/采集/订单）都连这同一个 Chrome 实例。
3. **唯一登录态目录**：`C:\Users\Administrator\WorkBuddy\chrome-cdp-profile`
   - 易店助手 + 闲鱼的 Cookie 全存这个目录，**登录一次永久有效**
   - 禁止换目录、禁止删除该目录、禁止在里面清缓存
   - ⚠️ 2026-09-13 从 Edge 切换到 Chrome，Cookie 不通用，**需要重新扫码登录一次**，之后永久有效
4. **每次任务第一步**：跑环境自检脚本（9222 活着就直接复用，绝不重启）：
```powershell
cd C:\Users\Administrator\.workbuddy\skills\xianyu-service-publish\scripts
C:\Users\Administrator\.workbuddy\binaries\python\envs\default\Scripts\python.exe ensure_chrome.py
```
5. **只在一种情况下需要扫码**：第一次使用，或平台强制踢下线。登录后 Cookie 已持久化，下次任务**直接连，不要让用户重登**。
6. **发布宝贝 = 易店助手**。禁止登 goofish.com 闲鱼后台发布（那是备用通道，仅易店助手挂掉时经用户确认才用）。
7. Chrome 启动命令唯一固定（自己手写时也必须带这三样）：
```powershell
Start-Process "C:\Program Files\Google\Chrome\Application\chrome.exe" -ArgumentList "--remote-debugging-port=9222","--remote-allow-origins=*","--user-data-dir=C:\Users\Administrator\WorkBuddy\chrome-cdp-profile","https://ed.weeeg.com/ekadmin/index"
```

> **⚠️ 沙盒限制（2026-09-15 修订，必读）**：沙盒内启动的浏览器会在命令结束时被回收，且不加豁免会静默失败。
> **用户明确要求（2026-09-15）：浏览器一律 AI 自己启动，禁止让用户手动操作。**
> 正确做法（2026-09-15 实测唯一可靠）：用 **危险模式豁免（dangerouslyDisableSandbox=true）+ run_in_background=true 前台常驻启动**，靠后台任务保活：
> ```bash
> exec "/c/Program Files/Google/Chrome/Application/chrome.exe" --remote-debugging-port=9222 --remote-allow-origins=* --user-data-dir="C:\\Users\\Administrator\\WorkBuddy\\chrome-cdp-profile" "https://ed.weeeg.com"
> ```
> ❌ 实测无效的方式：`& disown`、cmd start、Python DETACHED_PROCESS/CREATE_BREAKAWAY_FROM_JOB——命令结束都会被回收。
> 注意：本环境 **PowerShell 工具 stdout 捕获不稳定**（输出为空不代表失败），启动后务必用 Bash curl 验证端口存活。
> 只有扫码登录这类必须人操作的环节才找用户；桌面「启动浏览器.exe」仅作备用。

---

## 🚫 合规红线（最高优先级，违反会被下架/封号）

**2026-08 实测：用户 49 个在售宝贝因违禁被平台全部下架，处罚 7 天。以下红线永久生效：**

1. **境外AI工具名一个字都不能出现**：ChatGPT、Claude、Codex、Midjourney 等（标题/描述/主图任何位置都不行，触发「未备案生成式AI服务」违禁）
2. **🚫 模型部署/模型服务类永久禁发**：任何「模型部署」「模型服务」「AI本地部署」「AI服务器」「AI助手部署」——描述里**一个字的「模型/部署/服务」都不要写**（风控把国产大模型部署也归入违禁）
3. **🚫 无人机培训/考证类永久禁发**：「培训」「考证」「CAAC」「AOPA」「包过」「保过」涉及职业资质不当宣传。无人机只保留：维修、航拍、编队表演、定制DIY（文案不得提考证/证照/持证）
4. **「持证飞行」「持CAAC执照」等字样有风险**：即使服务本身合法（如景区航拍），描述里也不要写持证，用「专业飞手」「多年飞行经验」替代
5. **🚫 标题绝对不能出现「批量生产」**（2026-09-17 用户亲口强调）：四个字都不要出现，也不可用「批量产」「量产」等变体；表达规模化能力用「可接多单」「高效交付」替代
6. **🚫 AI托管/代刷类永久禁发**（2026-09-17 实测处罚）：商品被判「AI托管违禁风险」，命中规则「非法服务、票证、违反公序良俗类 > 不当获取流量或人气」——代刷粉丝/听众/排行/流量、代拉新推广、顶帖删帖、代网络投票等一概不碰；描述里不得出现「托管」「代刷」「代涨粉」「刷流量」等字样
7. **🚫 医疗代办类永久禁发**（2026-09-19 实测处罚）：商品被判「代挂号违禁风险」，命中规则「非法服务、票证、违反公序良俗类 > 不适宜开展的代办类服务」——**「代挂」两个字绝对不要写**，也不得写代挂号、代预约、代排队、就诊代排队、产科建档等任何医疗代办字样；同类禁发还有：代办车牌/驾照/进京证/经营许可证/认证证书、代补贴申请、代驾照扣分、代写党政类文档。医疗相关只能写合规服务（如陪诊陪护需极其谨慎、不涉及挂号排队），拿不准就不发
8. **描述不能含 emoji**（✅等触发校验报错），用【】和 - 替代
9. **发布前每个商品自查一遍**以上红线

**每类商品发布注意**：分类优先「其他闲置」；系统识别出更合适且支持网页发布的分类（如「DeepSeek服务」「AI数字人」）可用；图片上传后等约6秒再展开分类下拉才能看到「其他闲置」完整分类树。

**易店助手通道补充红线（v3.0）：**

7. **卡密类商品需确认合法来源**（卡券系统的卡号/卡密需有合法授权，禁售盗版资源）
8. **采集他人商品需确认不侵犯知识产权**（商品采集模块使用时注意）
9. **自动回复内容不得含违禁词**（智能回复配置时自查，同第1-3条红线）
10. **不暴露易店助手账号密码**（脚本不硬编码，用配置文件）
11. **批量操作防风控**：连续改开关每行间隔 ≥1.5秒；批量上下架分小批执行

---

## 模式 K：易店助手发布商品（v4.0 主通道，发布一律走这里）

在易店助手后台（ed.weeeg.com/ekadmin/product/add_product）填表发布，**不需要闲鱼登录**，发布完的商品自动进易店管理体系（模式 E 开自动发货等）。

### 第 1 步：环境自检（每次必做）
```powershell
cd C:\Users\Administrator\.workbuddy\skills\xianyu-service-publish\scripts
C:\Users\Administrator\.workbuddy\binaries\python\envs\default\Scripts\python.exe ensure_chrome.py
```
- 输出「已在运行 -> 直接复用」即就绪；未运行会自动用固定登录态目录启动 Chrome
- 易店登录态失效时才需要用户扫码（登录一次永久保存，别让用户重复登）

### 第 2 步：主图（2026-09-15 升级：即梦 AI 直出为首选）

**首选：即梦 AI 主图 `scripts/gen_main_image.py`**（需 New API 网关 127.0.0.1:3000 在线，即梦服务开机自启）
- 模型不硬编码：每次从网关 `/v1/models` 自动选最强生图模型（pro 优先 > 版本号高优先 > lite 垫底；2026-09-15 实测选中 jimeng-image-5.0-pro）
- 图内文字只放服务名（≤8 字才写进图；超长自动改无文字图）；**不放价格**（改价不用重出图）
- 实拍场景感提示词库，按服务类型匹配：photo/video/drone/repair/ai/design
- 提示词自动过滤境外 AI 工具名（合规红线，见下）
- 用法：`python gen_main_image.py --name "无人机航拍" --type drone --tags 4K,航拍 --out-dir <主图目录>`
- **批量接入**：数据文件图片字段写 `AUTO`（或 `AUTO:drone` 指定场景类型），`ed_publish_batch.py` 自动先生图再发布；每商品出 2 张候选，第 1 张直接用，第 2 张留底可换
- **质检（AI 职责）**：生图后逐张用视觉能力检查文字错字/遮挡/乱码；两张都有问题→重生一次；仍不行→降级用代码卡片，保证发布不卡壳

**备选：代码卡片**（即梦服务挂掉/批量铺货图省事时用），用 `scripts/make-service-card.ps1` 代码绘制（参数用法见 `references/legacy-goofish-direct.md` 模式 A 第 2 步）。

### 第 3 步：单商品发布（代码调用）
```python
import sys; sys.path.insert(0, r"C:\Users\Administrator\.workbuddy\skills\xianyu-service-publish\scripts")
from ed_publish import EDPublish

pub = EDPublish()
pub.connect()
log = pub.publish({
    "title": "【宜昌】电商产品拍摄 主图/详情页/短视频",   # ≤30字，遵守合规红线
    "desc": "完整描述（不含第一行标题，同样遵守红线、无emoji）",
    "image": r"C:\path\card.png",
    "price": "68",
    "stock": "10",
    "category": "其他闲置",
    "city": ["湖北省", "宜昌市"],
    "shipping": "无需邮寄",
}, dry_run=True)   # ⚠️ 第一次一律 dry_run=True 预览填表结果，给用户确认后再 False 真发
pub.close()
```

### 第 4 步：批量发布
```powershell
cd C:\Users\Administrator\.workbuddy\skills\xianyu-service-publish\scripts
C:\Users\Administrator\.workbuddy\binaries\python\envs\default\Scripts\python.exe ed_publish_batch.py <数据文件> <主图目录> [起始序号] [只跑N个] [dry]
```
- 数据文件格式与旧版通用：`名称|图片.png|价1|价2|价3|` + 描述块
- 日志在同目录 `ed-publish-log.txt`
- 先 `dry` 跑一个验证填表，再真跑

### ⚠️ 经验
- `dry_run=True` 只填表不点发布，**首次发布必须先 dry 预览**
- 商品分类选「其他闲置」（合规红线一致）
- 易店表单的「所属店铺」下拉选第一项即可（单店铺）
- 发布后看 `check_result()` 返回：URL 离开 add_product 或出现成功提示 = 成功
- 发布成功的商品立刻可在模式 E 商品列表看到，可直接开自动发货开关

---

## 模式 A/B/C：goofish.com 备用直发通道（⚠️ 仅易店助手不可用时，经用户确认后启用）

发布首选永远是模式 K（易店助手）。备用通道要点速记：
- **模式 A 单发**：goofish.com/publish 网页填表，同一 Chrome 9222 + 同一 profile，描述第一行即标题，含中文 eval 一律 base64 传输
- **模式 B 批量**：`scripts/publish_batch.py`（先 `--check` 自检），数据文件格式与易店批量通用
- **模式 C 万能提示词**：给朋友账号用，读 `assets/universal-prompt.md`，替换城市后生成腾讯文档交付

完整 JS 填表序列、分类选择、地址弹窗处理等细节 → 读 `references/legacy-goofish-direct.md`（需用时才读）

## 模式 E：易店助手商品管理（v3.0 新增）

通过 CDP 驱动易店助手后台管理已发布的商品（goofish 直发和易店发布的商品都在这里统一管理）。

### 前置条件
0. 先跑环境自检：`python ensure_chrome.py`（见环境铁律；9222 已在运行就直接复用）
1. Chrome 以 CDP 模式启动并登录易店助手：
```powershell
Start-Process "C:\Program Files\Google\Chrome\Application\chrome.exe" -ArgumentList "--remote-debugging-port=9222","--remote-allow-origins=*","--user-data-dir=C:\Users\Administrator\WorkBuddy\chrome-cdp-profile","https://ed.weeeg.com/ekadmin/index"
```
2. 用户扫码登录易店助手后台

### 运行脚本
```powershell
cd C:\Users\Administrator\.workbuddy\skills\xianyu-service-publish\scripts
C:\Users\Administrator\.workbuddy\binaries\python\envs\default\Scripts\python.exe ed_product.py
```

### 常用操作
```python
from ed_product import EDProduct
p = EDProduct()
p.connect()

# 1. 读取出售中商品列表（含开关状态）
products = p.list_products(status="出售中", max_rows=50)
# 返回 [{idx,id,shop,title,price,exposure,views,wants,auto_ship,resell,bargain,published,updated}]

# 2. 按状态筛选：出售中/已下架/已售罄/已配置发货/未配置发货/定时上架
p.list_products(status="已下架")

# 3. 按关键词搜索
p.search_product("拍摄")

# 4. 开关总览统计
overview = p.view_switch_overview()  # 统计自动发货/售罄上架/小刀的开启数

# 5. 设置某行开关（⚠️ 会真实改动，需用户确认）
p.set_row_switch(0, "auto_ship", True)   # 开第0行自动发货
p.set_row_switch(1, "resell", True)      # 开第1行售罄自动上架
p.set_row_switch(2, "bargain", True)     # 开第2行2人小刀

# 6. 批量设置开关（⚠️ 会真实改动，需用户确认）
p.batch_set_switches(rows=[0,1,2], auto_ship=True, resell=True, bargain=True)

# 7. 行内「更多」菜单（真实鼠标 hover 触发 el-dropdown）
menu_items = p.row_more(0)               # 返回菜单：配置发货 | 编辑商品 | 复制商品 | 下架宝贝 | 删除商品
p.row_more(0, "配置发货")                  # 点击配置发货菜单项（打开配置弹窗）

# 8. 打开某行的「配置发货」弹窗（通过行内自动发货开关点击）
p.open_config_ship_dialog(0)              # 弹窗 LABELS:发货类型|商品规格|发货方式|网盘内容|消息模板|自动发货状态

# 9. 批量操作（⚠️ dry_run=True 只勾选预览，安全）
p.batch_action(rows=[0,1,2], action="上下架", dry_run=True)
```

### 开关列说明（行内 3 个开关）
| 索引 | 名称 | 作用 |
|---|---|---|
| 0 | 自动发货 | 买家付款后自动发发货内容（需先配置发货模板） |
| 1 | 售罄自动上架 | 商品售罄后自动重新上架 |
| 2 | 2人小刀 | 两人以上砍价自动同意 |

---

## 模式 J：订单管理与统计（v3.0 P3 新增）

查看订单、评价管理、销售统计。

### 运行脚本
```powershell
cd C:\Users\Administrator\.workbuddy\skills\xianyu-service-publish\scripts
C:\Users\Administrator\.workbuddy\binaries\python\envs\default\Scripts\python.exe ed_order.py
```

### 常用操作
```python
from ed_order import EDOrder
o = EDOrder()
o.connect()

# 1. 读取订单列表
orders = o.list_orders(status="全部")
# status: 全部/待付款/待发货/待收货/退款中/交易完成/交易关闭/黑名单/待评价
# 返回 [{idx, shop, order_id, product, user, amount, qty, status, pay_time, remark}]

# 2. 切换订单状态
o.switch_order_status("待发货")

# 3. 订单状态概览（各待处理订单数）
summary = o.get_order_summary()

# 4. 销售统计
stats = o.get_sales_stats()  # 销售订单/金额/退款/购买用户 + 今日/昨日/环比

# 5. 去评价管理
o.goto_evaluation()

# 6. 商品统计 tab
o.open_stat_page(tab="商品统计")

o.close()
```

### 统计卡片说明
| 指标 | 内容 |
|---|---|
| 销售订单(笔) | 今日/昨日/日环比/成交订单总量 |
| 销售金额(元) | 今日/昨日/日环比/销售总额 |
| 退款金额(元) | 今日/昨日/日环比/本月退款 |
| 购买用户 | 今日/昨日/日环比/总用户数 |
| 状态角标 | 待付款/待发货/待收货/退款中 |
| 图表 | 营业趋势/订单来源分析/订单类型分析 |

---

## 模式 H：商品采集（v3.0 P2 新增）

从其他闲鱼店铺或官方采集商品到自己店铺（适合扩规模）。

### 运行脚本
```powershell
cd C:\Users\Administrator\.workbuddy\skills\xianyu-service-publish\scripts
C:\Users\Administrator\.workbuddy\binaries\python\envs\default\Scripts\python.exe ed_collect.py
```

### 常用操作
```python
from ed_collect import EDCollect
c = EDCollect()
c.connect()

# 1. 按关键词搜索商品
results = c.search(keyword="拍摄", qtype="店铺商品")
# 返回 [{idx, shop, product_id, title, price, published}]

# 2. 批量按ID采集（核心功能：从总商品.txt 里读 ID 列表）
ids = ["1077487223816", "1079912988993"]
c.collect_by_ids(ids, publish_mode="存草稿", dry_run=True)
# publish_mode: 立即发布 / 存草稿

# 3. 单行添加到采集列表
c.add_single_to_list(row_idx=0)

# 4. 批量添加到采集列表（需先勾选多行）
c.select_result_row(0, checked=True)
c.batch_add_to_list()

# 5. 去采集日志查看进度
c.goto_log()

# 6. 去商品草稿查看已采集待发布
c.goto_draft()

c.close()
```

### 批量采集配置项
- **商品ID列表**：textarea（支持逗号/空格/换行分隔）
- **采集平台**：闲鱼
- **同步发货**：checkbox（勾选则新发布商品自动配置发货）
- **鱼小铺**：checkbox
- **自定义配置**：使用默认配置 / 使用自定义配置（可改分类/城市/库存/价格/成本）
- **发布店铺**：select
- **发布方式**：立即发布 / 存草稿

### ⚠️ 经验
- dry_run=True 只填表不点「开始采集」，安全预览
- 真实采集前需选「发布店铺」
- 易店只能从闲鱼采集（不能从淘宝/其他平台）
- 商品ID必须是闲鱼商品ID（不是淘宝/拼多多ID）

---

## 模式 I：卡券系统（v3.0 P2 新增）

管理卡卷（虚拟商品/网盘资源用的卡号卡密）。

### 运行脚本
```powershell
cd C:\Users\Administrator\.workbuddy\skills\xianyu-service-publish\scripts
C:\Users\Administrator\.workbuddy\binaries\python\envs\default\Scripts\python.exe ed_card.py
```

### 常用操作
```python
from ed_card import EDCard
card = EDCard()
card.connect()

# 1. 读取卡卷列表
cards = card.list_cards(status="全部")
# status: 全部/未使用/已使用/使用中
# 返回 [{idx, id, name, kind, no, secret(脱敏), status, order_id, used_by, used_at, created_at}]

# 2. 打开添加卡卷弹窗（自动跳过绑定邮箱）
dlg = card.open_add_card()

# 3. 填卡种名称（第一步）
card.fill_card_kind_name("试用资料包", dry_run=True)
card.close_add_card_dialog()

# 4. 切换到卡种管理
card.switch_to_kind_manage()

card.close()
```

### 添加卡卷两步流程
1. **第一步**：输入卡种名称（自动判断新建或已有）
2. **第二步**：选填报方式（文本导入/文件导入/系统生成）
   - 文本导入：粘贴卡号+卡密（每行一个，空格/tab分隔）
   - 文件导入：上传 CSV/Excel
   - 系统生成：自动生成卡号卡密
3. 点「确定」完成

### ⚠️ 经验
- 写操作前会自动遇到「绑定邮箱」弹窗，脚本会跳过
- 卡卷列表 11 个字段：ID/名称/卡类/卡号/卡密/状态/购买订单ID/使用人/使用时间/创建时间/操作
- 状态机：全部→未使用→已使用→使用中

---

## 模式 G：智能回复配置（v3.0 P1 新增）

通过 CDP 驱动易店助手管理智能回复规则，降低客服成本。

### 运行脚本
```powershell
cd C:\Users\Administrator\.workbuddy\skills\xianyu-service-publish\scripts
C:\Users\Administrator\.workbuddy\binaries\python\envs\default\Scripts\python.exe ed_reply.py
```

### 常用操作
```python
from ed_reply import EDReply
r = EDReply()
r.connect()

# 1. 读取所有智能回复规则
rules = r.list_rules()
# 返回 [{idx, id, keyword, type, content_type, match_rule, products, shops, exclude, content, enabled}]

# 2. 添加关键词回复（dry_run=True 只填表不点确定，dry_run=False 实际添加）
r.add_rule({
    "trigger_type": 0,      # 0关键词回复 1首次回复 2系统消息
    "match_type": 1,        # 0无匹配 1包含 2等于
    "keywords": ["价格", "多少钱"],
    "content_type": 1,      # 1文本消息 2图片消息 3文本+图片
    "reply_text": "您好，本店服务定价请看主页详情",
    "scope": 0,             # 0全部通用 1指定店铺/商品
    "enabled": True
}, dry_run=True)

# 3. 切换某行规则开关
r.toggle_rule(row_idx=0, enabled=False)

# 4. 列出智能回复子菜单（自动回复/AI智能回复/回复配置/模板管理/黑名单/图片管理）
r.list_reply_submenu()

r.close()
```

### 添加回复弹窗字段
| 字段 | 类型 | 取值 |
|---|---|---|
| 触发方式 | radio-button | 0关键词回复 / 1首次回复 / 2系统消息 |
| 触发规则 | radio-button | 0无匹配 / 1包含 / 2等于 |
| 关键词 | tag-input | 输入后回车添加，最多20个 |
| 内容类型 | radio-button | 1文本消息 / 2图片消息 / 3文本+图片 |
| 回复文本 | textarea | 25/500 字 |
| 适用范围 | radio-button | 0全部通用 / 1指定店铺/商品 |
| 排除商品 | 按钮 | 点「+ 添加排除商品」 |
| 开启状态 | switch | 默认开 |

### ⚠️ 经验
- 添加回复弹窗所有控件都是 el-radio-button（按钮式单选），用真实鼠标点击切换
- 关键词用真实键盘 Input.dispatchKeyEvent 逐字符输入 + 回车
- 回复文本用 execCommand('insertText', false, text) 注入（支持中文）
- 免费版可能限制智能回复功能（自动回复开关被后端拒）

---

## 模式 F：鱼店配置管理（v3.0 新增）

管理易店助手的全局开关（自动发货/自动回复/免拼发货等）。

### 运行脚本
```powershell
cd C:\Users\Administrator\.workbuddy\skills\xianyu-service-publish\scripts
C:\Users\Administrator\.workbuddy\binaries\python\envs\default\Scripts\python.exe ed_config.py
```

### 常用操作
```python
from ed_config import EDConfig
cfg = EDConfig()
cfg.connect()

# 1. 读取全部配置（三个标签页：基础设置/消息设置/高级功能）
all_cfg = cfg.read_all()

# 2. 单项开关设置（⚠️ 会真实改动，需用户确认）
cfg.set_auto_ship(True)        # 自动发货：启用
cfg.set_auto_reply(True)       # 自动回复：启用
cfg.set_mianpin(True)          # 免拼发货：启用
cfg.set_card_send(True)        # 卡卷单发：启用
cfg.set_error_notify(True)     # 异常通知：启用
cfg.set_auto_flower(False)     # 自动求花：关闭
cfg.save()                     # 必须点保存才生效！

# 3. 批量配置（一次性保存）
plan = {
    "基础设置": {"自动发货": True, "自动回复": True, "免拼发货": True},
    "消息设置": {"订单发货后发给买家": True},
}
changes = cfg.batch_configure(plan)
```

### 配置项说明
| 标签页 | 配置项 | 说明 |
|---|---|---|
| 基础设置 | 自动发货 | 买家付款后自动发货（**核心**，需商品已配置发货内容） |
| 基础设置 | 自动回复 | 开启后买家消息自动回复（需配合模式 G 配置回复规则） |
| 基础设置 | 免拼发货 | 拼单自动免拼发货（免费版不更新拼单状态直接发货） |
| 基础设置 | 卡卷单发 | 卡券发给买家后再单独发一次 |
| 基础设置 | 异常通知 | 不发货/状态异常时邮件通知 |
| 基础设置 | 自动评价 | 跳转评价配置 |
| 基础设置 | 自动求花 | 发货后自动向买家求小红花 |
| 消息设置 | 订单发货/收货/退款中 | 各状态通知买家开关 |
| 高级功能 | 发货声明 | 发货附加声明 |

### ⚠️ 关键经验（2026-08 实测）
- 开关是 **el-radio-group**（启用=value 1 / 关闭=value 0），不是 el-switch
- 修改后**必须点「保存」按钮**才生效
- 保存后自动发货等开关**可能被重置为关闭**，需二次读取确认
- 配置完**不要刷新页面**（刷新会重置开关状态）

---

## 模式 L：搜索可见性诊断（v4.2 新增，纯读取零风控）

怀疑商品被限流/没曝光时用：以买家视角搜关键词，看自家商品在前 3 页的排名。

```powershell
cd C:\Users\Administrator\.workbuddy\skills\xianyu-service-publish\scripts
C:\Users\Administrator\.workbuddy\binaries\python\envs\default\Scripts\python.exe check_visibility.py "关键词" --ids 商品ID1,商品ID2
```

- 原理：在 9222 的 Chrome 新开 goofish.com 搜索页，滚动加载约 60 个结果，比对你的商品 ID
- 判定：前 20 名=权重正常；21-60=权重偏低；找不到=强限流信号（再用 ID 直搜复核，ID 能搜到而关键词搜不到=确认搜索降权）
- 商品 ID 从模式 E 的 `list_products()` 拿
- ⚠️ 只读操作（搜索=正常浏览），但别高频跑，一天几次足矣
- 诊断后的归因与修复打法 → 读 `references/xianyu-risk-and-reply.md` 第三节

---

## 文案转化法则（发布必经，v4.1 吸收自 @尚工在吗 xianyu-listing-pro）

闲鱼转化靠「标题搜得到 + 文案信得过 + 话术接得住」。写标题/描述时必守：

1. **标题**：≤30 字，前 15 字放主搜词；结构 = 核心词+长尾词+场景词
2. **正文结构**：痛点开场 → 解决方案 → 信任状（案例/经验）→ 价格锚点 → 催促行动
3. **话术**：常备「能便宜吗/怎么发货/正版吗」三类自动回复（配置到模式 G）
4. **FAQ 堵退款**：在描述尾部提前回答 3-5 个常见质疑
5. **三类语气**：虚拟资料（强调自动发货秒到）/ 实物新品（强调保障）/ 二手闲置（强调成色真实）
6. **文案红线**：不编销量好评（「已售1000+」类必须标真实数据）；不引导站外交易；虚拟商品注明「非实物」

> 深挖运营打法（流量机制/定价阶梯/诊断漏斗/竞品分析）→ 读 `references/xianyu-ops-playbook.md`（可选支线，源自 @Lenny xianyu-service-ops，MIT）
> 改价改标题/被限流诊断/回买家议价 → 读 `references/xianyu-risk-and-reply.md`（可选支线，源自 goofish-cli 内置技能，Apache 2.0）

## 描述文案模板（服务类通用）

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

## 已踩坑位清单（Top 8 必记，全文见 references/pitfalls.md）

1. 「其他服务」分类网页版发不了 → 必须选「其他闲置」
2. PowerShell 脚本含中文必须 UTF-8 BOM，否则乱码闪退
3. 描述不能含 emoji（校验报错），用【】和 - 替代
4. 价格 input 是 React 受控组件 → 原生 setter + dispatch input/change
5. 页面必须在前台（`bringToFront()`），后台标签页 CDP 鼠标事件被丢弃
6. el-loading-mask 残留会挡住所有点击 → 先 `clear_loading_masks()`
7. 每条 CDP/浏览器命令单独执行、逐条检查返回值，禁止 `&&` / `;` 链接
8. 鱼店配置改完必须点「保存」且不要刷新页面，保存后二次读取确认

其余 21 条（上传/下拉/单选/弹窗/API 端点等排障细节）→ `references/pitfalls.md`

## 项目结构

```
xianyu-service-publish/
├── SKILL.md                        # 技能定义（触发词 + 完整操作手册）
├── README.md                       # 本文件
├── README_EN.md                    # English README
├── .env.example                    # 环境变量示例
├── assets/
│   └── universal-prompt.md         # 万能发布提示词模板（给朋友用，朋友走 goofish 无易店）
├── references/                     # 深度参考文档（需用时才读）
│   ├── service-library.md          # 33项服务完整文案库（拍摄剪辑8/无人机5/AI类9/生活类7/节点类3/老照片修复，每项含主图参数+价格+完整描述）
│   ├── legacy-goofish-direct.md    # （v4.2 外置）goofish.com 备用直发完整流程：模式 A/B/C 的 JS 填表序列、分类选择、地址弹窗处理
│   ├── pitfalls.md                 # （v4.2 外置）已踩坑位完整清单 29 条（主文件只留 Top 8）
│   ├── xianyu-ops-playbook.md      # 运营打法手册（流量机制/关键词/定价阶梯/诊断漏斗/竞品分析；v4.1 吸收自 @Lenny xianyu-service-ops，MIT）
│   ├── xianyu-risk-and-reply.md    # 风控与客服话术手册（闲气值/流量池/降价改标/议价阶梯/人设语气；v4.1 吸收自 goofish-cli 内置技能，Apache 2.0）
│   ├── creator-platform.md         # 闲鱼创作者平台手册（author.goofish.com 发帖规范/人设/热点/内容红线；2026-09-20 官方要求整理）
│   └── 已废弃-xb-commands.md       # （已过时，v2.x xb CLI 时代参考，仅存档）
└── scripts/                        # 全部自动化脚本
    ├── ensure_chrome.py            # ⭐ 环境自检（每次任务第一步：复用/启动 Chrome 9222，固定登录态目录）
    ├── ed_publish.py               # ⭐ 模式K 易店单商品发布（填表/传图/发布/结果判定）
    ├── ed_publish_batch.py         # ⭐ 模式K 易店批量发布（断点续跑/日志/防风控间隔）
    ├── cdp_tools.py                # 易店助手 CDP 通用工具库（连接/eval/导航/表格/开关操作）
    ├── ed_product.py               # 模式E 商品管理自动化（列表/筛选/搜索/开关/批量操作）
    ├── ed_config.py                # 模式F 鱼店配置自动化（自动发货/自动回复/免拼发货等开关）
    ├── ed_reply.py                 # 模式G 智能回复配置（添加/读取/切换规则）
    ├── ed_collect.py               # 模式H 商品采集自动化（搜索/批量ID/发布或存草稿）
    ├── ed_card.py                  # 模式I 卡券系统自动化（卡卷列表/添加卡密/卡种管理）
    ├── ed_order.py                 # 模式J 订单统计自动化（订单列表/状态/销售统计）
    ├── check_visibility.py         # 模式L 搜索可见性诊断（买家视角搜关键词，判定限流）
    ├── gen_main_image.py           # 即梦 AI 主图生成模块（自动选最强模型，实拍场景库，AUTO 接入批量发布）
    ├── make-service-card.ps1       # 服务卡片主图生成脚本（参数化，UTF-8 BOM）
    ├── publish_batch.py            # （备用）goofish 直发批量驱动（Chrome CDP 9222；先跑 `--check` 自检）
    └── （其余为排障探针脚本：probe_*.py / fix_price.py / try_prices.py / verify_all.py 等）
```

## 注意事项

- **环境强绑定 Windows + Chrome**：所有路径、启动命令、登录态目录均为 Windows 环境实测配置，其他平台需自行适配
- **Python 依赖**：`requests`、`websocket-client`，使用 WorkBuddy 内置 Python 环境（`C:\Users\Administrator\.workbuddy\binaries\python\envs\default\Scripts\python.exe`）
- **即梦 AI 主图依赖 New API 网关**（127.0.0.1:3000）在线；网关不可用时自动降级为代码卡片方案
- **合规红线是硬约束**：2026-08 曾因违禁导致 49 个在售宝贝全部下架 + 处罚 7 天，发布前必须逐条自查
- **写操作前必须用户确认**：开关改动、批量发布、规则添加等真实写操作一律先 `dry_run` 预览并经用户确认
- **免费版易店助手可能限制部分功能**（如智能回复自动开关被后端拒绝）
- **登录态目录神圣不可动**：勿删、勿换、勿清缓存，否则需要重新扫码登录

## 许可证

MIT License

## 作者

sheen945
