# 闲鱼服务类商品·万能批量发布提示词（模板）

> 使用方法：把「【开始】」到「【结束】」之间的内容整段复制，粘贴到 QClaw 或 WorkBuddy 对话里发送即可。AI 会在你自己的闲鱼账号上逐个发布这些服务类商品。
> ⚠️ 用之前把【宜昌】替换成你自己的城市。

---

【开始】

# 任务：闲鱼服务类商品批量发布

请在**我自己的闲鱼账号**（当前登录的账号）上，帮我逐个发布下面列出的全部服务类商品。这是服务类商品，不是实物商品。

## 第零步：先检查你的环境

1. 确认你能控制浏览器（打开网页、点击、填表、上传文件）。如果当前环境没有浏览器自动化能力，请**先告诉我**，不要直接放弃。
2. 确认闲鱼网页版已登录**我自己的账号**（打开 https://www.goofish.com 检查右上角是否是我本人的昵称）。
3. 准备好存放主图的文件夹（例如 `C:\Users\Administrator\.qclaw\workspace\temp\relaunch3\`，不存在就创建）。

## 第一步：先读规则（非常重要，违规会被下架封号）

### 绝对禁止出现的词（出现在标题/描述/主图任何一个地方都不行）
1. **境外AI工具名**：ChatGPT、Claude、Codex、Midjourney 等（一个字母都不能出现）
2. **模型部署/服务类字样**：模型部署、模型服务、AI本地部署、AI服务器、AI助手部署（描述里不要写「部署」两个字）
3. **培训/考证/证照承诺**：无人机培训、考证、CAAC、AOPA、持证飞行、持CAAC执照、包过、保过（涉及职业资质的不当宣传会被下架）
4. **emoji**：描述里不能用任何 emoji 表情符号（用【】和 - 替代）
5. 以上每发布一个商品前，都自查一遍

### 每类商品发布时注意
- 分类：优先选「其他闲置」；如果系统自动识别出更合适的分类（如「DeepSeek服务」「AI数字人」）且支持网页发布，可用识别分类
- 图片上传后等约6秒（让系统识别完成），再展开分类下拉，此时才能看到「其他闲置」（完整分类树）；如果下拉里没有「其他闲置」，关闭重开，最多3次
- 发布前会弹「宝贝所在地精准地址」选择窗，选一个常用地址即可（如没有，选你所在城市的地址）

## 第二步：准备主图

每张主图用代码绘制（**不要用AI生图**，AI生图中文会乱码）。使用下面的 PowerShell 脚本生成，每个商品一张，保存到你的主图文件夹（先创建目录）：

脚本保存为 `make-service-card.ps1`，**必须用 UTF-8 BOM 编码保存**（否则中文乱码）。生成方法：
```
powershell -ExecutionPolicy Bypass -File make-service-card.ps1 -OutPath "输出路径.png" -Title "主标题" -SubTitle "副标题" -Price1 "价格1" -Price1Label "档位1" -Price2 "价格2" -Price2Label "档位2" -Price3 "价格3" -Price3Label "档位3" -Desc "服务特点一句话" -Note "拍前请先私聊沟通需求" -Region "宜昌市区上门 / 全国远程" -Tag1 "标签1" -Tag2 "标签2" -Tag3 "标签3" -Badge "徽标文字"
```

脚本内容（完整复制保存，见技能目录 scripts/make-service-card.ps1，或按下面内嵌版本）：

```powershell
# 闲鱼服务类商品主图生成脚本（代码绘制，避免AI生图中文字乱码）
# 必须 UTF-8 BOM 编码保存
param(
    [string]$OutPath = "xianyu-service-card.png",
    [string]$Title = "服务标题",
    [string]$SubTitle = "副标题",
    [string]$Price1 = "68", [string]$Price1Label = "基础版",
    [string]$Price2 = "128", [string]$Price2Label = "套餐版",
    [string]$Price3 = "", [string]$Price3Label = "",
    [string]$Desc = "一对一服务 · 不满意免费重做",
    [string]$Note = "拍前请先私聊沟通需求",
    [string]$Region = "宜昌市区上门 / 全国远程",
    [string]$Tag1 = "专业服务", [string]$Tag2 = "包教包会", [string]$Tag3 = "售后保障",
    [string]$Badge = "SERVICE"
)
Add-Type -AssemblyName System.Drawing
$W=800;$H=800
$bg=[System.Drawing.Color]::FromArgb(24,26,42)
$cardBg=[System.Drawing.Color]::FromArgb(38,42,66)
$yellow=[System.Drawing.Color]::FromArgb(255,185,0)
$white=[System.Drawing.Color]::White
$gray=[System.Drawing.Color]::FromArgb(180,185,205)
$lightGray=[System.Drawing.Color]::FromArgb(120,125,150)
$bmp=New-Object System.Drawing.Bitmap($W,$H)
$g=[System.Drawing.Graphics]::FromImage($bmp)
$g.SmoothingMode=[System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$g.TextRenderingHint=[System.Drawing.Text.TextRenderingHint]::AntiAlias
$g.Clear($bg)
# 顶部徽标
$f=New-Object System.Drawing.Font("Microsoft YaHei",14,[System.Drawing.FontStyle]::Bold)
$b=New-Object System.Drawing.SolidBrush($yellow)
$g.DrawString($Badge,$f,$b,40,36)
# 主标题
$f=New-Object System.Drawing.Font("Microsoft YaHei",40,[System.Drawing.FontStyle]::Bold)
$b=New-Object System.Drawing.SolidBrush($white)
$g.DrawString($Title,$f,$b,40,90)
# 副标题
$f=New-Object System.Drawing.Font("Microsoft YaHei",20,[System.Drawing.FontStyle]::Regular)
$b=New-Object System.Drawing.SolidBrush($gray)
$g.DrawString($SubTitle,$f,$b,40,165)
# 标签行
$tagY=220;$xPos=40
foreach($tag in @($Tag1,$Tag2,$Tag3)){
    $f=New-Object System.Drawing.Font("Microsoft YaHei",14,[System.Drawing.FontStyle]::Bold)
    $b=New-Object System.Drawing.SolidBrush($white)
    $bg2=New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(58,62,92))
    $g.FillRectangle($bg2,$xPos,$tagY,118,36)
    $g.DrawString($tag,$f,$b,$xPos+12,$tagY+4)
    $xPos+=140
}
# 三档价格卡片
$cardY=300;$cardW=220;$cardH=180;$cardGap=20;$cx=40
foreach($card in @(@{P=$Price1;L=$Price1Label},@{P=$Price2;L=$Price2Label},@{P=$Price3;L=$Price3Label})){
    $b=New-Object System.Drawing.SolidBrush($cardBg)
    $g.FillRectangle($b,$cx,$cardY,$cardW,$cardH)
    $f=New-Object System.Drawing.Font("Microsoft YaHei",30,[System.Drawing.FontStyle]::Bold)
    $b=New-Object System.Drawing.SolidBrush($yellow)
    $g.DrawString($card.P,$f,$b,$cx+20,$cardY+20)
    $f=New-Object System.Drawing.Font("Microsoft YaHei",15,[System.Drawing.FontStyle]::Bold)
    $b=New-Object System.Drawing.SolidBrush($white)
    $g.DrawString($card.L,$f,$b,$cx+20,$cardY+75)
    $f=New-Object System.Drawing.Font("Microsoft YaHei",12,[System.Drawing.FontStyle]::Regular)
    $b=New-Object System.Drawing.SolidBrush($lightGray)
    $g.DrawString($Region,$f,$b,$cx+20,$cardY+120)
    $cx+=$cardW+$cardGap
}
# 底部特点+提示+装饰条
$f=New-Object System.Drawing.Font("Microsoft YaHei",18,[System.Drawing.FontStyle]::Bold)
$b=New-Object System.Drawing.SolidBrush($white)
$g.DrawString($Desc,$f,$b,40,540)
$f=New-Object System.Drawing.Font("Microsoft YaHei",14,[System.Drawing.FontStyle]::Regular)
$b=New-Object System.Drawing.SolidBrush($gray)
$g.DrawString($Note,$f,$b,40,590)
$b=New-Object System.Drawing.SolidBrush($yellow)
$g.FillRectangle($b,40,700,720,6)
$bmp.Save($OutPath,[System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose();$bmp.Dispose()
Write-Output "图片已生成: $OutPath"
```

## 第三步：发布流程（每个商品重复以下步骤）

1. 打开 `https://www.goofish.com/publish`
2. 用 eval 把隐藏的文件上传框显示出来（display:block; position:fixed; top/left 10px; opacity:0.01），给它加 id 和 aria-label
3. 截图/快照找到上传框的引用，上传对应商品的主图
4. **等约6秒**，让系统识别图片分类
5. 展开分类下拉，选「其他闲置」；如果下拉里没有，关闭重开（最多3次）
6. 在描述框（第一行即标题）填入商品文案
7. 填价格（第一个框为主价，有多个档位就填多个框）
8. 点「发布」，如果弹出「宝贝所在地」选择窗，选常用地址
9. 验证：页面跳转到商品详情页（URL 含 item?id=）即发布成功
10. 发布下一个商品前，自查一遍文案没有违规词

## 第四步：商品清单（34项，含主图参数与完整文案）

【这里按需插入商品清单：每项包含主图生成参数（Title/SubTitle/Badge/Tag/Price）和完整描述文案。可参考技能内置文案库 references/service-library.md，或由用户提供】

## 第五步：发布后验证

- 打开个人中心确认商品在「在售」列表
- 或打开卖家工作台 seller.goofish.com 查看商品管理
- 把发布结果汇总报告给我（每个商品的标题/价格/链接）

## 注意事项

- 34个商品建议分2-3批发布，每批10-15个，批间间隔1-2小时，避免触发风控
- 商品文案里所有【宜昌】替换成我的城市（或按我提供的城市修改）
- 全程不要发布：AI模型部署类、无人机培训/考证类商品（红线）

【结束】

---

## 生成提示词时的操作指引（给 AI 自己）

1. 复制本模板，把【这里按需插入商品清单】替换成实际商品清单
2. 商品清单来源：`references/service-library.md`（33项）+ 用户自定义项
3. 城市占位符【宜昌】保留，告诉用户可批量替换
4. 交付：创建腾讯文档（create_smartcanvas_by_mdx）+ manage.set_privilege policy=3（任何人可编辑），把链接给用户
