# 已踩坑位完整清单（30条）

> 从 SKILL.md v4.2 外置。主文件只保留最关键的 8 条；做 CDP 填表/排障时读全文。

---



1. **「其他服务」分类网页版发不了** → 弹扫码APP提示，必须选「其他闲置」
1.5. **闲鱼圈子网页版发不了**（2026-09-19 实测：goofish.com 全站无圈子/发帖入口）→ 圈子帖只能手机 App 手动发，AI 只负责产出文案
1.6. **批量改文案走易店编辑页**：`add_product/{商品ID}` 直达，复用 EDPublish 的 fill_title/fill_desc/click_button('保存') 即可，约15秒/条，197条零失败；保存=触发一次擦亮（免费刷曝光）；列表翻页用 list_products(max_rows=500, max_pages=20) 才能拉全量（2026-09-19 实测 203 条在售）
2. **AI生图中文乱码** → 服务卡片图必须 PowerShell 代码绘制
3. **PowerShell 脚本含中文必须 UTF-8 BOM** → 否则 GBK 乱码闪退
4. **file input 是隐藏的** → 先 eval 改 display 再 snapshot 拿 ref 才能 upload；页面重开后 ref 失效需重新 snapshot
5. **type 多行文本会被 shell 转义吃掉** → 用 execCommand insertText 注入 contenteditable
6. **radio 普通 click 不生效** → 用 JS 点 label 元素
7. **antd 下拉普通 click 不生效** → elementFromPoint + 派发 pointerdown/mousedown/pointerup/mouseup/click 完整事件序列
8. **upload/click 的 ref 不带 @ 前缀**；upload 支持 CSS 选择器（先 eval 设 data-testid）
9. **闲鱼一口价只能一个价** → 主价填引流价，多档价写描述+主图
10. **每条 CDP/浏览器命令单独执行、逐条检查返回值**，禁止 `&&` / `;` 链接
11. **发布时可能弹「宝贝所在地」选择窗** → 点常用地址（如民欣家园B区），选完自动关闭
12. **商品描述不能包含 emoji** → 校验报错，去掉后重填
13. **价格 input 用原生 setter 填值**（React 受控组件）→ setter + dispatch input/change
14. **境外AI工具名是违禁词**（ChatGPT/Claude/Codex/Midjourney）→ 触发「未备案生成式AI服务」下架
15. **skillhub 发布页 Radix UI Popover 分类选择** → JS click 不生效，需 focus + 完整事件序列，选项是 checkbox
16. **🚫 模型部署/模型服务类永久禁发**（2026-08-05 用户亲口强调）→ 描述里一个字的模型/部署/服务都不要写
17. **🚫 无人机培训/考证类永久禁发**（2026-08-05 用户亲口强调）→ 培训/考证/CAAC/AOPA 一律不上
17b. **🚫 标题禁含「批量生产」**（2026-09-17）→ 触发平台风控；「AI托管/代刷流量/代涨粉」类服务及字样永久禁发，命中「不当获取流量或人气」规则会被判违禁处罚
18. **图片上传后分类树两态** → 前5秒推荐分类（无其他闲置），约6秒后完整分类树；下拉打开状态下识别完成不会刷新，需关闭重开
19. **批量发布用 Node.js 驱动** → PowerShell 5.1 参数解析 bug（数组拆参/左括号报错），Node 数组传参彻底规避
21. **页面必须在前台** — Chrome 后台标签页会丢弃 CDP 模拟鼠标事件，所有操作前 `bringToFront()`
22. **加载遮罩拦截** — el-loading-mask 残留时 elementFromPoint 命中 mask，挡住所有点击；`clear_loading_masks()` 移除
23. **el-radio 必须点圆点** — 点 label 文字不一定生效，点 `.el-radio__inner` 圆点最稳
24. **保存前需 removeClass** — 表单数据已变但未保存，刷新会重置。沛神建议：保存后立即验证，必要时重新点
25. **免费版功能限制** — 鱼店配置开关会被后端拒绝并提示「免费版不支持XXX，请升级权益」；捕获 el-message 检查拒绝原因
26. **行内 el-switch 点击后弹配置对话框** — 不是直接切换，是触发「设置2人小刀」「批量设置发货」等弹窗（待进一步调试）
27. **真实鼠标 hover 触发 el-dropdown** — `el-dropdown` 必须用 CDP `Input.dispatchMouseEvent` 真实鼠标事件才能展开，DOM `mouseenter` 无效
28. **行内开关=配置发货入口** — 点击行内「自动发货/售罄上架/2人小刀」开关会打开该商品的「配置发货」弹窗（LABELS:发货类型|商品规格|发货方式|网盘内容|消息模板|自动发货状态），不是直接 toggle
29. **API 端点** — 配置发货弹窗由 `PUT /adminapi/product/product/set_show/<id>/<0|1>` 触发；商品详情由 `GET /adminapi/product/product/<id>?...` 获取
