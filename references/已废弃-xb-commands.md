# xb CLI 命令参考（闲鱼发布场景）

> ⛔ **2026-09-13 已废弃，不要再用**：本机浏览器方案已统一为
> **Google Chrome + CDP 9222 + 固定目录 `chrome-cdp-profile`**（见 `chrome-browser` 技能）。
> 闲鱼 SKILL.md 环境铁律第 1 条也明确禁止 QClaw `xb` CLI。
> 本文件仅保留作历史对照，实际干活一律用：
> - 环境自检 `scripts/ensure_chrome.py`
> - 易店发布 `scripts/ed_publish.py` / `ed_publish_batch.py`
> - 闲鱼直发（备用）`scripts/publish_batch.py`

xb 脚本路径：`C:\Users\Administrator\.qclaw\skills\xbrowser\scripts\xb.cjs`（已弃用）
每次任务第一步：`node scripts/xb.cjs init` 检查环境。（已弃用）

## 命令结构（重要）

- 顶层命令：`init`、`run`、`config`、`guide`、`status`、`setup`、`stop`、`cleanup`、`shield`、`version`、`help`
- `snapshot`、`click`、`wait`、`screenshot`、`type`、`upload`、`eval` 等都是 `run` 的子命令：
  ```
  node scripts/xb.cjs run --browser cft snapshot -i
  node scripts/xb.cjs run --browser cft click e31
  ```
- 每条命令单独执行，禁止 `&&`、`;` 链接；逐条检查 JSON 返回
- `--browser` 必须指定：`cft`（内置，登录态可复用）/ `chrome` / `edge` / `qqbrowser`，用错浏览器需重新登录
- 有头模式加 `--headed`；xb 级选项（--browser、--headed、--timeout）放在 action verb 之前
- URL 建议单引号包裹防 shell 解析
- ref 不带 @ 前缀（snapshot 文档里的 @ref 是写法示意）

## 常用命令

### 导航
```
run --browser cft open "https://www.goofish.com/publish"
run --browser cft wait --load networkidle    # 等待页面加载完成
run --browser cft get url                     # 获取当前URL
run --browser cft reload
```

### 页面结构
```
run --browser cft snapshot -i                 # 交互式元素快照（拿ref）
run --browser cft get text <ref>              # 获取元素文本
run --browser cft get value <ref>             # 获取表单值
run --browser cft get html <ref>              # 获取innerHTML
run --browser cft eval "<JS表达式>"           # 执行JS（返回JSON.stringify结果）
```

### 交互操作
```
run --browser cft click <ref>
run --browser cft type <ref> "文本"           # 注意：多行会被shell转义吃掉
run --browser cft press Enter                 # 按键
run --browser cft press Control+A             # 全选
run --browser cft upload <ref> "文件路径"     # 文件上传（ref需可见）
run --browser cft scroll down 400             # 滚动
run --browser cft scroll up 400
run --browser cft focus <ref>
```

### 截图
```
run --browser cft screenshot                  # 截图（路径在返回JSON里）
run --browser cft screenshot --full-page      # 整页截图
```

### 会话管理
```
stop <browser> --force        # 关闭浏览器
cleanup                       # 清理会话
status                        # 环境状态
```

## 常用 JS 片段（闲鱼发布页）

### 定位隐藏 file input 并显示
```js
(()=>{const i=document.querySelector('input[type=file]');i.style.cssText='display:block;position:fixed;top:0;left:0;width:50px;height:50px;opacity:0.01;z-index:99999';return 'ok'})()
```

### 点击 antd 下拉选项（分类选择）
```js
(()=>{const opts=Array.from(document.querySelectorAll('.ant-select-item-option-content'));const t=opts.find(e=>e.textContent.trim()==='其他闲置');if(!t)return 'NOT_FOUND';t.closest('.ant-select-item').click();return 'CLICKED'})()
```

### 注入多行文本到 contenteditable（描述框）
```js
(()=>{const el=document.querySelector('[contenteditable]');el.focus();document.execCommand('selectAll',false,null);const txt='多行\n文本';document.execCommand('insertText',false,txt);return 'INSERTED:'+txt.length})()
```

### 点击 label 选中 radio（运费）
```js
(()=>{const ls=Array.from(document.querySelectorAll('label')).filter(l=>l.innerText&&l.innerText.trim()==='无需邮寄');if(!ls.length)return 'NOT_FOUND';ls[0].click();return 'CLICKED'})()
```

### 检查 radio 选中状态
```js
JSON.stringify(Array.from(document.querySelectorAll('input[type=radio]')).map(r=>({checked:r.checked,label:r.closest('label')?r.closest('label').innerText.trim():''})).filter(x=>x.label))
```

## 错误处理

| 错误 | 处理 |
|---|---|
| 操作超时 | `run --timeout 29000 ...`（上限29s） |
| 元素引用失效 | 重新 `snapshot -i` 拿新 ref |
| 浏览器已关闭 | `init` 后重新 open |
| 截图文件在工作区外 | 先复制到 workspace 再给 image 工具分析 |
| 登录态丢失 | 截图给用户，引导扫码登录 |

## 图片分析注意

统一方案（`chrome-browser`：Chrome CDP 9222）截图时**直接把文件写到工作区目录**，省去复制步骤：

```python
page.screenshot(path=r"C:\Users\Administrator\WorkBuddy\<当前项目目录>\temp\check.png")
```

> ⚠️ 2026-09-13：旧的 QClaw `xb` CLI / `agent-browser` 截图目录
> `C:\Users\Administrator\.agent-browser\tmp\screenshots\` **已废弃**，
> 技能里已禁止使用 `xb` CLI；一律走 `chrome-browser` 技能。
