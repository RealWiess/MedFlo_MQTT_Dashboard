---
name: Brand Identity & Presentation Design
description: 建立品牌識別系統或製作產品簡報時使用。包含品牌指南模板（色彩、字型、聲調）、Logo 設計原則、企業識別規範、HTML 簡報設計策略、投影片版型指南。
---

# 品牌識別與簡報設計 (Brand Identity & Presentation Design)

> **來源**：改編自 [ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) 的 `brand` + `design` + `slides` skills
> **適配**：重寫為 Antigravity IDE skill 格式

---

## 適用場景

當你被要求進行以下任務時，啟動此 skill：

- 建立新產品或公司的品牌識別系統
- 設計 Logo、選擇品牌色彩和字型
- 製作產品簡報 / Pitch Deck / 投影片
- 製作社群媒體圖片 / Banner
- 撰寫品牌指南文件 (Brand Guideline)
- 品牌一致性審查

**宣告**：「我正在使用 Brand Identity & Presentation skill 來建立品牌規範。」

---

## 1. 品牌指南模板 (Brand Guideline Template)

### 1.1 Quick Reference Card

每個品牌指南的開頭必須包含：

```markdown
# [品牌名稱] Brand Guidelines v1.0

## Quick Reference
- **Primary Color:** #XXXXXX
- **Secondary Color:** #XXXXXX
- **Primary Font:** {font-family}
- **Brand Voice:** {3 個關鍵特質，例如：專業、溫暖、可信賴}
```

### 1.2 色彩系統 (Color Palette)

| 類型 | 要定義的項目 | 說明 |
|------|------------|------|
| **Primary** | 1-2 色 | 品牌主色，用於 CTA、標題、Logo |
| **Secondary** | 1-2 色 | 輔助色，用於次要元素、強調 |
| **Neutral** | 4-6 色 | 灰階，用於背景、文字、邊框 |
| **Semantic** | 3-4 色 | 成功(綠)、警告(黃)、錯誤(紅)、資訊(藍) |

**每個色彩必須記錄**：
```markdown
| 名稱 | Hex | RGB | 用途 |
|------|-----|-----|------|
| MedFlow Blue | #2563EB | rgb(37,99,235) | 主要品牌色、CTA 按鈕、標題 |
```

**無障礙要求**：
- 文字 / 背景對比度 ≥ 4.5:1 (WCAG AA)
- CTA 按鈕對比度 ≥ 3:1

### 1.3 字型系統 (Typography)

```css
--font-heading: 'Inter', 'Noto Sans TC', sans-serif;
--font-body: 'Inter', 'Noto Sans TC', sans-serif;
--font-mono: 'JetBrains Mono', monospace;
```

| 元素 | 字型 | 字重 | 大小 (桌面/手機) | 行高 |
|------|------|------|-----------------|------|
| H1 | Heading | 700 | 36px / 28px | 1.2 |
| H2 | Heading | 600 | 28px / 24px | 1.3 |
| H3 | Heading | 600 | 22px / 20px | 1.3 |
| Body | Body | 400 | 16px / 16px | 1.6 |
| Caption | Body | 400 | 14px / 12px | 1.5 |

### 1.4 品牌聲調 (Brand Voice)

定義品牌的溝通風格，用三個維度描述：

| 維度 | 我們是 | 我們不是 |
|------|--------|---------|
| 語氣 | 專業但親切 | 冷冰冰的 |
| 用詞 | 簡潔明瞭 | 學術術語堆砌 |
| 態度 | 值得信賴的 | 誇大其辭的 |

---

## 2. Logo 設計原則

### 2.1 設計要求

- **簡潔**：在 16x16 favicon 到看板大小都清晰可辨
- **可擴展**：向量格式 (SVG) 優先
- **對比**：淺色/深色背景都能使用
- **留白**：Logo 周圍最少保留 Logo 高度 50% 的安全區域

### 2.2 Logo 變體

每個品牌應準備：

| 變體 | 用途 |
|------|------|
| **Full Logo** (圖標 + 文字) | 官方文件、網站 Header |
| **Icon Only** (圖標) | Favicon、App Icon、社群頭像 |
| **Wordmark** (純文字) | 窄空間、Footer |
| **Monochrome** (單色) | 印刷、浮水印 |

### 2.3 色彩心理學快速參考

| 色彩 | 聯想 | 適合產業 |
|------|------|---------|
| 藍色 | 信任、專業、科技 | 醫療、金融、科技 |
| 綠色 | 健康、成長、自然 | 醫療、環保、農業 |
| 紫色 | 創新、高端、智慧 | 教育、奢侈品 |
| 橘色 | 活力、友善、創意 | 娛樂、食品 |
| 黑色 | 高端、權威、經典 | 時尚、法律 |

> **MedFlow 建議**：醫療 + 科技 → 藍色為主色搭配綠色點綴，傳達「專業信賴 + 健康照護」

---

## 3. 簡報設計 (Presentation Design)

### 3.1 簡報結構策略

| 策略 | 結構 | 適合場景 |
|------|------|---------|
| **Problem-Solution** | 痛點 → 方案 → 優勢 → CTA | 產品 Pitch |
| **Data Story** | 數據 → 洞察 → 行動 | 投資人報告 |
| **Before-After** | 現狀 → 變革 → 成果 | 轉型案例 |
| **Timeline** | 起源 → 里程碑 → 未來 | 公司介紹 |

### 3.2 投影片版型規則

**每頁投影片必須遵循**：

1. **一頁一概念**：每張投影片只傳達一個核心訊息
2. **6×6 規則**：最多 6 行文字，每行最多 6 個詞
3. **視覺優先**：圖 > 圖表 > 列表 > 段落文字
4. **對比強烈**：標題和內文的大小差距至少 1.5 倍
5. **留白充足**：內容區域不超過頁面面積的 60%

### 3.3 HTML 簡報產生

使用純 HTML/CSS 產生簡報（可在瀏覽器直接打開）：

```html
<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=1280, height=720">
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    .slide {
      width: 1280px;
      height: 720px;
      padding: 80px;
      page-break-after: always;
      position: relative;
      font-family: 'Inter', 'Noto Sans TC', sans-serif;
    }
    .slide h1 { font-size: 48px; font-weight: 700; margin-bottom: 24px; }
    .slide p { font-size: 24px; line-height: 1.6; color: #6B7280; }
  </style>
</head>
<body>
  <div class="slide" style="background: linear-gradient(135deg, #1E3A5F, #2563EB);">
    <h1 style="color: white;">標題頁</h1>
    <p style="color: rgba(255,255,255,0.8);">副標題或 Tagline</p>
  </div>
  <div class="slide">
    <h1>問題</h1>
    <p>描述目標受眾面臨的痛點...</p>
  </div>
</body>
</html>
```

### 3.4 圖表整合 (Chart.js)

簡報中需要數據視覺化時：

```html
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<canvas id="chart1" width="600" height="400"></canvas>
<script>
new Chart(document.getElementById('chart1'), {
  type: 'bar',  // bar, line, pie, doughnut
  data: {
    labels: ['Q1', 'Q2', 'Q3', 'Q4'],
    datasets: [{
      label: '銷售額',
      data: [120, 190, 300, 500],
      backgroundColor: 'rgba(37, 99, 235, 0.8)'
    }]
  }
});
</script>
```

---

## 4. 社群媒體 / Banner 尺寸速查

| 平台 | 類型 | 尺寸 (px) |
|------|------|----------|
| **Facebook** | 封面 | 1200 × 630 |
| **Facebook** | 貼文 | 1200 × 1200 |
| **Instagram** | 貼文 | 1080 × 1080 |
| **Instagram** | 限時動態 | 1080 × 1920 |
| **LinkedIn** | 封面 | 1584 × 396 |
| **LinkedIn** | 貼文 | 1200 × 627 |
| **Twitter/X** | Header | 1500 × 500 |
| **Twitter/X** | 貼文 | 1200 × 675 |
| **YouTube** | 縮圖 | 1280 × 720 |
| **YouTube** | Banner | 2560 × 1440 |

---

## 5. 品牌一致性檢查清單

每次產出品牌相關素材後，必須核對：

- [ ] 色彩是否使用品牌指南定義的 Hex 值？
- [ ] 字型是否使用指定的 font-family？
- [ ] Logo 是否保留足夠的安全區域？
- [ ] 文字/背景對比度是否符合 WCAG AA？
- [ ] 品牌聲調是否一致（不過度正式或過度隨意）？
- [ ] 所有尺寸是否符合目標平台的規格？
