---
name: Web UI Design System (Token + Component)
description: 建立 Web App / Dashboard 時使用。包含三層 Design Token 架構（Primitive→Semantic→Component）、元件規格、shadcn/ui + Tailwind CSS 最佳實踐、Dark Mode、響應式設計、無障礙設計規範。
---

# Web UI Design System

> **來源**：改編自 [ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) 的 `design-system` + `ui-styling` skills
> **適配**：重寫為 Antigravity IDE skill 格式，去除 Claude Code 特定依賴

---

## 適用場景

當你被要求進行以下任務時，啟動此 skill：

- 建立 Web App / Dashboard 的 UI
- 使用 React / Next.js / Vite 框架的前端開發
- 需要建立 Design System 或 Design Token
- 實作 Dark Mode / 主題切換
- 建立響應式佈局
- 需要無障礙 (Accessibility) 的元件設計

**宣告**：「我正在使用 Web UI Design System skill 來確保設計一致性。」

---

## 1. Design Token 三層架構

所有視覺屬性必須使用 CSS 變數 (Custom Properties)，分為三層：

```
┌─────────────────────────────────────────┐
│  Component Tokens                       │  元件級覆寫
│  --button-bg, --card-padding            │
├─────────────────────────────────────────┤
│  Semantic Tokens                        │  語意別名（主題切換靠這層）
│  --color-primary, --spacing-section     │
├─────────────────────────────────────────┤
│  Primitive Tokens                       │  原始設計值
│  --color-blue-600, --space-4            │
└─────────────────────────────────────────┘
```

### 1.1 Primitive Tokens（原始值）

```css
:root {
  /* === Colors === */
  --color-gray-50: #F9FAFB;
  --color-gray-100: #F3F4F6;
  --color-gray-200: #E5E7EB;
  --color-gray-300: #D1D5DB;
  --color-gray-500: #6B7280;
  --color-gray-700: #374151;
  --color-gray-900: #111827;

  --color-blue-50: #EFF6FF;
  --color-blue-500: #3B82F6;
  --color-blue-600: #2563EB;
  --color-blue-700: #1D4ED8;

  --color-green-500: #22C55E;
  --color-red-500: #EF4444;
  --color-amber-500: #F59E0B;

  /* === Spacing (4px base unit) === */
  --space-1: 0.25rem;   /* 4px */
  --space-2: 0.5rem;    /* 8px */
  --space-3: 0.75rem;   /* 12px */
  --space-4: 1rem;      /* 16px */
  --space-6: 1.5rem;    /* 24px */
  --space-8: 2rem;      /* 32px */
  --space-12: 3rem;     /* 48px */
  --space-16: 4rem;     /* 64px */

  /* === Typography === */
  --font-sans: 'Inter', 'Noto Sans TC', system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', monospace;

  --text-xs: 0.75rem;    /* 12px */
  --text-sm: 0.875rem;   /* 14px */
  --text-base: 1rem;     /* 16px */
  --text-lg: 1.125rem;   /* 18px */
  --text-xl: 1.25rem;    /* 20px */
  --text-2xl: 1.5rem;    /* 24px */
  --text-3xl: 1.875rem;  /* 30px */

  /* === Border Radius === */
  --radius-sm: 0.25rem;
  --radius-md: 0.375rem;
  --radius-lg: 0.5rem;
  --radius-xl: 0.75rem;
  --radius-full: 9999px;

  /* === Shadows === */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
}
```

### 1.2 Semantic Tokens（語意層 — 主題切換靠這層）

```css
/* Light Theme */
:root, [data-theme="light"] {
  --color-bg: var(--color-gray-50);
  --color-bg-card: white;
  --color-bg-elevated: white;
  --color-text: var(--color-gray-900);
  --color-text-muted: var(--color-gray-500);
  --color-border: var(--color-gray-200);
  --color-primary: var(--color-blue-600);
  --color-primary-hover: var(--color-blue-700);
  --color-success: var(--color-green-500);
  --color-danger: var(--color-red-500);
  --color-warning: var(--color-amber-500);
}

/* Dark Theme */
[data-theme="dark"] {
  --color-bg: var(--color-gray-900);
  --color-bg-card: var(--color-gray-700);
  --color-bg-elevated: var(--color-gray-700);
  --color-text: var(--color-gray-50);
  --color-text-muted: var(--color-gray-300);
  --color-border: var(--color-gray-500);
  --color-primary: var(--color-blue-500);
  --color-primary-hover: var(--color-blue-600);
}
```

### 1.3 Component Tokens（元件級）

```css
:root {
  /* Button */
  --button-height: 2.5rem;
  --button-padding-x: var(--space-4);
  --button-radius: var(--radius-md);
  --button-font-weight: 500;

  /* Card */
  --card-padding: var(--space-6);
  --card-radius: var(--radius-lg);
  --card-shadow: var(--shadow-md);

  /* Input */
  --input-height: 2.5rem;
  --input-padding-x: var(--space-3);
  --input-radius: var(--radius-md);
  --input-border: 1px solid var(--color-border);
}
```

---

## 2. 元件規格 (Component Specs)

### 2.1 Button

| 變體 | 背景 | 文字 | 用途 |
|------|------|------|------|
| Primary | `--color-primary` | white | 主要動作 (Submit, Save) |
| Secondary | transparent | `--color-primary` | 次要動作 (Cancel) |
| Destructive | `--color-danger` | white | 破壞性動作 (Delete) |
| Ghost | transparent | `--color-text` | 工具列按鈕 |

**狀態**：
- `:hover` → 背景加深 10%
- `:focus-visible` → 2px ring，offset 2px
- `:disabled` → opacity 0.5，cursor not-allowed
- `:active` → scale(0.98)

### 2.2 Card

```css
.card {
  background: var(--color-bg-card);
  border-radius: var(--card-radius);
  padding: var(--card-padding);
  box-shadow: var(--card-shadow);
  border: 1px solid var(--color-border);
}
```

### 2.3 Form Input

```css
.input {
  height: var(--input-height);
  padding: 0 var(--input-padding-x);
  border: var(--input-border);
  border-radius: var(--input-radius);
  background: var(--color-bg-card);
  color: var(--color-text);
  transition: border-color 0.15s, box-shadow 0.15s;
}
.input:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
  outline: none;
}
```

### 2.4 Table

- Header: `font-weight: 600`, `background: var(--color-bg)`, `text-align: left`
- Row hover: `background: var(--color-bg)`
- Striped: 偶數行 `background: var(--color-bg)`
- Border: `border-bottom: 1px solid var(--color-border)`

---

## 3. 響應式斷點

```css
/* Mobile First */
--breakpoint-sm: 640px;    /* 手機 landscape */
--breakpoint-md: 768px;    /* 平板 */
--breakpoint-lg: 1024px;   /* 小筆電 */
--breakpoint-xl: 1280px;   /* 桌面 */
--breakpoint-2xl: 1536px;  /* 大螢幕 */
```

**佈局原則**：
- Mobile (< 640px): 單欄，堆疊佈局
- Tablet (768px+): 雙欄或側邊欄
- Desktop (1024px+): 完整佈局 + 側邊導航

---

## 4. 無障礙 (Accessibility) 必要規則

1. **對比度**：文字/背景至少 WCAG AA (4.5:1)，大文字 (3:1)
2. **焦點指示**：所有互動元素必須有 `:focus-visible` 樣式
3. **語意 HTML**：使用 `<button>` 而非 `<div onclick>`
4. **ARIA**：動態內容使用 `aria-live`，表單使用 `aria-label`
5. **鍵盤操作**：所有功能必須可用鍵盤完成

---

## 5. 技術棧建議

| 層級 | 推薦 | 備註 |
|------|------|------|
| 框架 | Next.js 或 Vite + React | SSR 用 Next.js，SPA 用 Vite |
| CSS | Tailwind CSS v4 + CSS Variables | 優先用 token 變數 |
| 元件庫 | shadcn/ui (Radix UI 基底) | 可自訂、無障礙、TypeScript |
| 字型 | Inter + Noto Sans TC | 中英混排最佳 |
| 圖表 | Chart.js 或 Recharts | Dashboard 用 |
| 動畫 | Framer Motion | 微動效增強體驗 |

### shadcn/ui 安裝

```bash
npx shadcn@latest init
npx shadcn@latest add button card dialog form table input
```

---

## 6. 反模式清單

| ❌ 不要 | ✅ 要 |
|---------|------|
| 寫死 `color: #2563EB` | 用 `color: var(--color-primary)` |
| 每個元件定義自己的間距 | 用 spacing token (`--space-4`) |
| 忽略 Dark Mode | 用 Semantic Token 層切換主題 |
| 用 `<div>` 做按鈕 | 用 `<button>` 或 `<a>` |
| 行內樣式 `style="..."` | 用 CSS class 或 Tailwind utilities |
| 忽略手機版面 | Mobile-first 設計，逐步增強 |
