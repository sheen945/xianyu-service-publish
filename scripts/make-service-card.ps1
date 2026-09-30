# 闲鱼服务类商品主图生成脚本（代码绘制，避免AI生图中文字乱码）
# 用法: powershell -ExecutionPolicy Bypass -File make-service-card.ps1 -OutPath "输出.png" [-Title "主标题"] [-SubTitle "副标题"] [-Price1 "¥200"] [-Price1Label "上门安装"] [-Price2 "¥50"] [-Price2Label "远程安装"] [-Price3 "¥499"] [-Price3Label "定制套餐"] [-Desc "服务特点一句话"]
# 注意: 本脚本必须用 UTF-8 BOM 编码保存（含中文），否则 PowerShell 5.1 会乱码

param(
    [string]$OutPath = "xianyu-service-card.png",
    [string]$Title = "AI软件上门安装服务",
    [string]$SubTitle = "DeepSeek / 通义千问 / 国产大模型",
    [string]$Price1 = "200",
    [string]$Price1Label = "上门安装",
    [string]$Price2 = "50",
    [string]$Price2Label = "远程安装",
    [string]$Price3 = "499",
    [string]$Price3Label = "定制套餐",
    [string]$Desc = "一对一服务 · 装好验收再付款",
    [string]$Note = "拍前请先私聊沟通需求",
    [string]$Region = "宜昌市区上门 / 全国远程",
    [string]$Tag1 = "AI部署",
    [string]$Tag2 = "远程调试",
    [string]$Tag3 = "包教包会",
    [string]$Badge = "AI INSTALL SERVICE"
)

Add-Type -AssemblyName System.Drawing

# ============ 布局参数 ============
$W = 800
$H = 800
$bg = [System.Drawing.Color]::FromArgb(24, 26, 42)      # 深蓝黑背景
$cardBg = [System.Drawing.Color]::FromArgb(38, 42, 66)  # 卡片背景
$yellow = [System.Drawing.Color]::FromArgb(255, 185, 0) # 主强调色(闲鱼黄)
$white = [System.Drawing.Color]::White
$gray = [System.Drawing.Color]::FromArgb(180, 185, 205) # 次级文字
$lightGray = [System.Drawing.Color]::FromArgb(120, 125, 150)

$bmp = New-Object System.Drawing.Bitmap($W, $H)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAlias
$g.Clear($bg)

# ============ 顶部徽标 ============
$badgeFont = New-Object System.Drawing.Font("Microsoft YaHei", 14, [System.Drawing.FontStyle]::Bold)
$badgeBrush = New-Object System.Drawing.SolidBrush($yellow)
$badgeRect = New-Object System.Drawing.RectangleF(40, 36, 400, 30)
$g.DrawString($Badge, $badgeFont, $badgeBrush, $badgeRect)

# ============ 主标题 ============
$titleFont = New-Object System.Drawing.Font("Microsoft YaHei", 40, [System.Drawing.FontStyle]::Bold)
$titleBrush = New-Object System.Drawing.SolidBrush($white)
$g.DrawString($Title, $titleFont, $titleBrush, 40, 90)

# ============ 副标题 ============
$subFont = New-Object System.Drawing.Font("Microsoft YaHei", 20, [System.Drawing.FontStyle]::Regular)
$subBrush = New-Object System.Drawing.SolidBrush($gray)
$g.DrawString($SubTitle, $subFont, $subBrush, 40, 165)

# ============ 图标标签行(3个) ============
$tagY = 220
$tags = @($Tag1, $Tag2, $Tag3)
$xPos = 40
foreach ($tag in $tags) {
    $tagFont = New-Object System.Drawing.Font("Microsoft YaHei", 14, [System.Drawing.FontStyle]::Bold)
    $tagBrush = New-Object System.Drawing.SolidBrush($white)
    $tagBg = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(58, 62, 92))
    $g.FillRectangle($tagBg, $xPos, $tagY, 118, 36)
    $g.DrawString($tag, $tagFont, $tagBrush, $xPos + 12, $tagY + 4)
    $xPos += 140
}

# ============ 三档价格卡片 ============
$cardY = 300
$cardW = 220
$cardH = 180
$cardGap = 20
$cards = @(
    @{ Price = $Price1; Label = $Price1Label },
    @{ Price = $Price2; Label = $Price2Label },
    @{ Price = $Price3; Label = $Price3Label }
)
$cx = 40
foreach ($card in $cards) {
    # 卡片背景
    $cardBrush = New-Object System.Drawing.SolidBrush($cardBg)
    $g.FillRectangle($cardBrush, $cx, $cardY, $cardW, $cardH)
    # 价格
    $priceFont = New-Object System.Drawing.Font("Microsoft YaHei", 30, [System.Drawing.FontStyle]::Bold)
    $priceBrush = New-Object System.Drawing.SolidBrush($yellow)
    $g.DrawString($card.Price, $priceFont, $priceBrush, $cx + 20, $cardY + 20)
    # 标签
    $labelFont = New-Object System.Drawing.Font("Microsoft YaHei", 15, [System.Drawing.FontStyle]::Bold)
    $labelBrush = New-Object System.Drawing.SolidBrush($white)
    $g.DrawString($card.Label, $labelFont, $labelBrush, $cx + 20, $cardY + 75)
    # 底部说明
    $descFont = New-Object System.Drawing.Font("Microsoft YaHei", 12, [System.Drawing.FontStyle]::Regular)
    $descBrush = New-Object System.Drawing.SolidBrush($lightGray)
    $g.DrawString($Region, $descFont, $descBrush, $cx + 20, $cardY + 120)
    $cx += $cardW + $cardGap
}

# ============ 底部服务特点 ============
$featureFont = New-Object System.Drawing.Font("Microsoft YaHei", 18, [System.Drawing.FontStyle]::Bold)
$featureBrush = New-Object System.Drawing.SolidBrush($white)
$g.DrawString($Desc, $featureFont, $featureBrush, 40, 540)

# ============ 底部提示 ============
$noteFont = New-Object System.Drawing.Font("Microsoft YaHei", 14, [System.Drawing.FontStyle]::Regular)
$noteBrush = New-Object System.Drawing.SolidBrush($gray)
$g.DrawString($Note, $noteFont, $noteBrush, 40, 590)

# ============ 底部装饰条 ============
$barBrush = New-Object System.Drawing.SolidBrush($yellow)
$g.FillRectangle($barBrush, 40, 700, 720, 6)

# ============ 保存 ============
$bmp.Save($OutPath, [System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose()
$bmp.Dispose()
Write-Output "图片已生成: $OutPath"
