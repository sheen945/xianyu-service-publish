# goofish.com 备用直发通道完整流程（v2.x 遗留）

> 从 SKILL.md v4.2 外置。仅当易店助手不可用且用户确认后才使用，平时不用读。
> 以下内容依赖闲鱼网页登录态（chrome-cdp-profile 里已登过）。

---

## 模式 A：单商品发布（⚠️ 备用通道，仅易店助手不可用时经用户确认使用；发布首选模式 K）

### 第 1 步：收集商品信息并确认
- 服务名称（标题用，≤20字）、价格方案（主推价/引流价/利润价，闲鱼只显示一个价）、服务内容要点、图片素材
- 标题技巧：城市+服务名+核心卖点，如「宜昌电商产品拍摄 专业布光 精修包满意」

### 第 2 步：制作商品主图（无实体图时）
首选即梦 AI 主图（见模式 K 第 2 步，`gen_main_image.py`，文字质检流程照做）；即梦不可用时用代码绘制服务卡片图：

```powershell
powershell -ExecutionPolicy Bypass -File "<skill_dir>\scripts\make-service-card.ps1" -OutPath "C:\...\card.png" -Title "电商产品拍摄" -SubTitle "主图/详情页/短视频" -Badge "PRODUCT PHOTO" -Tag1 "专业布光" -Tag2 "精修包满意" -Tag3 "48小时交付" -Price1 "68" -Price1Label "精修套餐" -Price2 "128" -Price2Label "含视频" -Price3 "" -Price3Label "" -Desc "一对一服务 · 不满意免费重拍" -Note "拍前请先私聊沟通需求" -Region "宜昌上门拍摄 / 全国远程"
```

全部参数可自定义：`-Badge` 顶部徽标、`-Tag1/2/3` 标签、`-Desc` 特点、`-Note` 提示、`-Region` 服务范围。脚本必须 UTF-8 BOM 编码保存（否则 PS5.1 中文乱码）。

### 第 3 步：浏览器初始化与登录（统一 Chrome CDP 9222，见环境铁律）
先跑 `ensure_chrome.py` 确认环境，然后直接用浏览器打开发布页。未登录时截图给用户扫码（Cookie 存固定 profile，登一次以后都有效）：

```powershell
# 复用 9222 的 Chrome 实例新开标签页（不要另起浏览器）
Start-Process "C:\Program Files\Google\Chrome\Application\chrome.exe" -ArgumentList "--remote-debugging-port=9222","--user-data-dir=C:\Users\Administrator\WorkBuddy\chrome-cdp-profile","https://www.goofish.com/publish"
```
- 后续填表用 Python CDP（`cdp_tools.py` 同款连接方式，目标 URL 匹配 `goofish.com`）驱动
- 若 goofish 登录态失效，让用户在该标签页里重新扫码一次即可（同一个 profile，登一次管两边）

### 第 4 步：填表与发布（关键操作序列）

> 以下 JS 片段是通用的，统一通过 Python CDP（`cdp_tools.py` 的 `eval()`）执行，不再用 xb CLI。每条命令单独执行、逐条检查返回值；禁止 `&&`/`;` 链接。
> 写法约定：`eval_js "..."` = 用 `EDClient().eval("...")` 执行该 JS；`snapshot -i` = 列出可交互元素拿引用；`upload <ref> <文件>` = 向该元素注入文件；`get_url` = `EDClient().get_url()` 读当前地址。

**① 上传主图（隐藏 file input）**
```powershell
# 1. eval 显示隐藏 input
eval_js "(()=>{const i=document.querySelector('input[type=file]');i.style.cssText='display:block;position:fixed;top:10px;left:10px;zIndex:99999;opacity:0.01;width:100px;height:30px';i.id='xianyu-upload';i.setAttribute('aria-label','xianyu-upload-input');return 'OK'})()"
# 2. snapshot 拿 ref（e31 通常不变，但每次页面重开需重新 snapshot）
snapshot -i
# 3. upload（ref 不带 @）
upload e31 "C:\...\card.png"
# 4. ⚠️ 等约6秒让图片识别完成（关键！否则分类下拉没有「其他闲置」）
```

**② 选分类（等6秒后展开，选「其他闲置」）**
```powershell
eval_js "(()=>{const sel=document.querySelector('.ant-select');if(!sel)return 'NO_SELECT';const r=sel.getBoundingClientRect();const x=r.left+r.width/2,y=r.top+r.height/2;const el=document.elementFromPoint(x,y);if(!el)return 'NO_EL';const o={bubbles:true,cancelable:true,view:window,clientX:x,clientY:y,button:0};['pointerdown','mousedown','pointerup','mouseup','click'].forEach(t=>{try{el.dispatchEvent(new MouseEvent(t,o))}catch(e){}});return 'OPENED'})()"
eval_js "(()=>{const o=[...document.querySelectorAll('.ant-select-item-option')];const t=o.find(x=>x.textContent.trim()==='其他闲置');if(!t)return 'NOT_FOUND';t.click();return 'PICKED'})()"
```
- 下拉无「其他闲置」→ 点 body 关闭 → 等2秒 → 重开，最多3次
- 下拉选项检查：`eval "(()=>[...document.querySelectorAll('.ant-select-item-option')].map(x=>x.textContent.trim()).join('|'))()"`
- 识别出更精准分类（DeepSeek服务/AI数字人等）且无「暂不支持」横幅时可直接用

**③ 填描述（contenteditable + base64 防乱码）**
```powershell
eval_js "(()=>{const ed=document.querySelector('div[contenteditable=true]');if(!ed)return 'NO_EDITOR';ed.focus();const r=document.createRange();r.selectNodeContents(ed);const s=window.getSelection();s.removeAllRanges();s.addRange(r);document.execCommand('insertText',false,decodeURIComponent(escape(atob('<BASE64描述>'))));return 'LEN:'+ed.textContent.length})()"
```
- 描述第一行即标题（闲鱼无独立标题字段）
- **含中文的 eval 一律用 base64 传输**（ConvertTo-Json/直接内嵌会报 SyntaxError）

**④ 填价格（React 受控组件用原生 setter）**
```powershell
eval_js "(()=>{const ins=[...document.querySelectorAll('input')].filter(i=>i.placeholder==='0.00');if(!ins.length)return 'NO_PRICE';const set=(el,v)=>{Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(el,String(v));el.dispatchEvent(new Event('input',{bubbles:true}));el.dispatchEvent(new Event('change',{bubbles:true}))};set(ins[0],'50');if(ins.length>1)set(ins[1],'200');return 'OK:'+ins.map(i=>i.value).join(',')})()"
```
- 单价的商品只填第1个框（如定做歌曲¥99、无人机维修¥100）

**⑤ 点发布 + 处理地址弹窗**
```powershell
eval_js "(()=>{const b=[...document.querySelectorAll('button')].find(b=>b.textContent.trim()==='发布');if(!b)return 'NO_BTN';b.click();return 'CLICKED'})()"
# 等3秒，检查地址弹窗
eval_js "(()=>{const d=document.querySelector('[role=dialog]');if(!d||d.style.display==='none')return 'NO_DIALOG';const items=[...d.querySelectorAll('[class*=addressItem]')];const t=items.find(i=>i.textContent.includes('民欣家园B区'));if(t){t.click();return 'CLICKED_ADDR'}return 'ADDR_ITEMS:'+items.map(i=>i.textContent.trim().substring(0,20)).join('|')})()"
# 有弹窗则再次点发布
```

**⑥ 成功判定**
```powershell
get_url
```
- URL 变为 `https://www.goofish.com/item?id=<新id>&categoryId=&spm=...` = 发布成功
- 仍在 publish 页 → 查 `eval "(()=>{const e=document.querySelector('.ant-form-item-explain-error');return e?('ERR:'+e.textContent.trim()):'NO_ERR'})()"` 定位错误

---

## 模式 B：批量发布（⚠️ 备用通道；批量发布首选模式 K 的 ed_publish_batch.py）

### 数据文件格式（data.md）
```
名称|主图文件名|价格1|价格2|价格3|
标题+描述（第一行即标题，可多行，空行分隔各商品块）
```
参考内置文案库 `references/service-library.md`（33项现成服务，含主图参数+价格+完整描述）。

### 驱动脚本（两条路）
- **首选：易店批量** `scripts/ed_publish_batch.py`（走易店助手，无需闲鱼登录，见模式 K）
- **备用：goofish 批量** `scripts/publish_batch.py`（Python，走统一 Chrome CDP 9222，仅在易店不可用时用）

```powershell
C:\Users\Administrator\.workbuddy\binaries\python\envs\default\Scripts\python.exe ed_publish_batch.py <数据文件> <主图目录> [起始序号] [只跑N个] [dry]
```

**为什么批量发布走易店**：数据文件格式两边通用，但易店通道不需要闲鱼登录态、不触发闲鱼网页风控、发布完自动进易店管理体系（自动发货/开关统一管理）。

### 已验证的经验（22个商品零失败跑通）
- 每个商品约 50 秒；批量间隔 2 秒（易店批量脚本内置 4 秒防风控间隔）
- 日志追加到同目录 `publish-batch-log.txt`（易店批量是 `ed-publish-log.txt`）
- 支持断点续跑：传入起始序号跳过已发布的
- 发布前**分批防风控**：34个分 2-3 批、每批 10-15 个、批间间隔 1-2 小时

---

## 模式 C：万能发布提示词（给朋友用）

用户想把服务清单交给朋友在**朋友自己的闲鱼账号**发布时，生成一份完整提示词：

1. 读取 `assets/universal-prompt.md` 模板
2. 把【宜昌】批量替换成朋友所在城市
3. 交付方式：创建腾讯文档（create_smartcanvas_by_mdx）+ 设置「任何人可编辑」（manage.set_privilege policy=3），把链接给用户转发

提示词结构（复制【开始】到【结束】粘贴给 AI 即可）：
- 第零步：环境检查（浏览器自动化能力/闲鱼登录/主图文件夹）
- 第一步：红线规则（禁止词清单）
- 第二步：主图生成（内嵌 make-service-card.ps1 完整脚本）
- 第三步：发布流程（10步详细操作）
- 第四步：商品清单（每项含主图参数+完整文案）
- 第五步：发布后验证

---
