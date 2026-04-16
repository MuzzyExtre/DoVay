# digtai.tech — Design System

> Полный справочник дизайна для переиспользования в других проектах.
> Стиль: **Cyberpunk / Neon-Tech** с тёмной и светлой темами.

---

## 1. Шрифты

| Роль | Шрифт | Начертания | CSS-переменная |
|------|--------|-----------|----------------|
| Display (заголовки, навигация, кнопки) | **Space Mono** (monospace) | 400, 700 | `--font-display` / `font-display` |
| Body (текст, описания) | **Outfit** (sans-serif) | 400, 700 | `--font-body` / `font-body` |

**Подключение (Next.js):**
```tsx
import { Space_Mono, Outfit } from "next/font/google";

const outfit = Outfit({
  variable: "--font-outfit",
  subsets: ["latin", "latin-ext"],
  weight: ["400", "700"],
  display: "swap",
});

const spaceMono = Space_Mono({
  variable: "--font-space",
  subsets: ["latin"],
  weight: ["400", "700"],
  display: "swap",
});

// В body: className={`${outfit.variable} ${spaceMono.variable} antialiased`}
```

**Типографика:**
- Заголовки H1: `font-display text-5xl md:text-6xl lg:text-7xl font-bold leading-[1.05] tracking-tight`
- Подзаголовки: `font-display text-xs uppercase tracking-[0.2em]`
- Навигация: `font-display text-xs uppercase tracking-widest`
- Параграфы: `text-base md:text-lg leading-relaxed text-text-mid`
- Мелкий текст: `font-display text-xs tracking-wider`

---

## 2. Цветовая палитра

### Dark Mode (по умолчанию)

| Токен | HEX | Tailwind | Назначение |
|-------|-----|----------|------------|
| `--color-void` | `#050508` | `bg-void` | Самый тёмный фон, body |
| `--color-ink` | `#0a0a10` | `bg-ink` | Чуть светлее, подложки |
| `--color-surface` | `#111118` | `bg-surface` | Карточки, поверхности |
| `--color-surface-raised` | `#17171f` | `bg-surface-raised` | Приподнятые элементы |
| `--color-surface-hover` | `#1e1e28` | `bg-surface-hover` | Ховер-состояния |
| `--color-neon-violet` | `#b48eff` | `text-neon-violet` | **Основной акцент** |
| `--color-neon-blue` | `#7cc4fa` | `text-neon-blue` | Вторичный акцент |
| `--color-neon-cyan` | `#4ee1d0` | `text-neon-cyan` | Третичный акцент |
| `--color-neon-pink` | `#f471b5` | `text-neon-pink` | Четвёртый акцент |
| `--color-text-bright` | `#eeeef0` | `text-text-bright` | Основной текст |
| `--color-text-mid` | `#9494a0` | `text-text-mid` | Вторичный текст |
| `--color-text-dim` | `#8a8a96` | `text-text-dim` | Приглушённый текст |
| `--color-line` | `#222230` | `border-line` | Границы, разделители |
| `--color-line-light` | `#2a2a3a` | `border-line-light` | Мягкие разделители |

### Light Mode (`html.light`)

| Токен | HEX |
|-------|-----|
| `--color-void` | `#f5f5f7` |
| `--color-ink` | `#ebebef` |
| `--color-surface` | `#ffffff` |
| `--color-surface-raised` | `#f0f0f4` |
| `--color-surface-hover` | `#e8e8ee` |
| `--color-neon-violet` | `#7c3aed` |
| `--color-neon-blue` | `#2563eb` |
| `--color-neon-cyan` | `#0891b2` |
| `--color-neon-pink` | `#db2777` |
| `--color-text-bright` | `#111118` |
| `--color-text-mid` | `#4b4b5a` |
| `--color-text-dim` | `#6b6b7a` |
| `--color-line` | `#d4d4dc` |
| `--color-line-light` | `#c8c8d0` |

---

## 3. Tailwind CSS конфиг

```css
/* globals.css */
@import "tailwindcss";

@theme {
  --color-void: #050508;
  --color-ink: #0a0a10;
  --color-surface: #111118;
  --color-surface-raised: #17171f;
  --color-surface-hover: #1e1e28;
  --color-neon-violet: #b48eff;
  --color-neon-blue: #7cc4fa;
  --color-neon-cyan: #4ee1d0;
  --color-neon-pink: #f471b5;
  --color-text-bright: #eeeef0;
  --color-text-mid: #9494a0;
  --color-text-dim: #8a8a96;
  --color-line: #222230;
  --color-line-light: #2a2a3a;
  --font-display: var(--font-space);
  --font-body: var(--font-outfit);
}
```

---

## 4. Компоненты UI

### 4.1 Glow Card (карточка с неоновым свечением)

```css
.glow-border {
  position: relative;
  background: var(--color-surface);
  border: 1px solid var(--color-line);
  transition: border-color 0.4s ease, box-shadow 0.4s ease;
}

.glow-border:hover {
  border-color: color-mix(in srgb, var(--color-neon-violet) 40%, transparent);
  box-shadow:
    0 0 20px -5px color-mix(in srgb, var(--color-neon-violet) 15%, transparent),
    inset 0 1px 0 0 color-mix(in srgb, var(--color-neon-violet) 8%, transparent);
}
```

**Использование:** `className="glow-border rounded-lg p-6 md:p-7"`

### 4.2 Tag Pill (метка/тег)

```css
.tag-pill {
  font-family: var(--font-display);
  font-size: 0.75rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  padding: 0.25rem 0.65rem;
  border: 1px solid var(--color-line);
  color: var(--color-text-mid);
  transition: all 0.3s ease;
}

.tag-pill:hover {
  border-color: var(--color-neon-violet);
  color: var(--color-neon-violet);
  background: color-mix(in srgb, var(--color-neon-violet) 6%, transparent);
}
```

### 4.3 Gradient Line (разделитель)

```css
.gradient-line {
  height: 1px;
  background: linear-gradient(
    90deg,
    transparent 0%,
    var(--color-neon-violet) 20%,
    var(--color-neon-cyan) 80%,
    transparent 100%
  );
}
```

### 4.4 Neon Hover (текст с неоновым свечением)

```css
.neon-hover {
  transition: color 0.3s ease, text-shadow 0.3s ease;
}
.neon-hover:hover {
  color: var(--color-neon-violet);
  text-shadow: 0 0 12px color-mix(in srgb, var(--color-neon-violet) 40%, transparent);
}
```

### 4.5 Dot Grid (фоновая сетка)

```css
.dot-grid {
  background-image: radial-gradient(circle, var(--color-line) 1px, transparent 1px);
  background-size: 24px 24px;
}
```

### 4.6 Terminal Prompt

```css
.terminal-prompt::before {
  content: "$ ";
  color: var(--color-neon-cyan);
  font-family: var(--font-display);
}
```

### 4.7 Typing Cursor

```css
.cursor-blink::after {
  content: "\2588";
  font-weight: 400;
  animation: blink 1s step-end infinite;
  color: var(--color-neon-violet);
  font-size: 0.9em;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}
```

---

## 5. Кнопки

### Primary (CTA)

```html
<a class="
  group flex items-center justify-center gap-2.5
  rounded-lg border border-neon-violet
  bg-neon-violet/10 px-7 py-3
  font-display text-xs uppercase tracking-widest text-neon-violet
  transition-all
  hover:bg-neon-violet/20
  hover:shadow-[0_0_30px_-5px] hover:shadow-neon-violet/30
">
  CTA Text
</a>
```

### Secondary (Ghost)

```html
<a class="
  flex items-center justify-center gap-2
  rounded-lg border border-line
  px-7 py-3
  font-display text-xs uppercase tracking-widest text-text-dim
  transition-all
  hover:border-text-dim hover:text-text-bright
">
  Secondary
</a>
```

### Nav CTA (компактная)

```html
<a class="
  group relative overflow-hidden
  rounded-lg border border-neon-violet/40
  bg-neon-violet/8 px-4 py-1.5
  font-display text-xs uppercase tracking-widest text-neon-violet
  transition-all
  hover:border-neon-violet
  hover:shadow-[0_0_20px_-5px] hover:shadow-neon-violet/30
">
  <span class="relative z-10">Button</span>
  <!-- Sweep-эффект при ховере -->
  <div class="
    absolute inset-0
    -translate-x-full bg-gradient-to-r
    from-transparent via-neon-violet/15 to-transparent
    transition-transform duration-500
    group-hover:translate-x-full
  "></div>
</a>
```

---

## 6. Навигация

### Desktop (pill-style с анимированным индикатором)

```
┌─────────────────────────────────────────────────┐
│  [01 SERVICES] [02 PROJECTS] [03 RATINGS] [04 CONTACT]  │
└─────────────────────────────────────────────────┘
```

**Стиль контейнера:**
```html
<div class="
  flex items-center rounded-full
  border border-line/50
  bg-surface/50 p-1
  backdrop-blur-sm
">
```

**Активный элемент (Framer Motion layoutId):**
```html
<motion.div
  layoutId="nav-pill"
  class="
    absolute inset-0 rounded-full
    border border-neon-violet/30
    bg-neon-violet/10
    shadow-[0_0_16px_-4px] shadow-neon-violet/20
  "
  transition={{ type: "spring", stiffness: 350, damping: 30 }}
/>
```

**Нумерация:**
- Активная: `text-neon-cyan text-[10px] tabular-nums`
- Неактивная: `text-text-dim/30 text-[10px] tabular-nums`

### Header (sticky)

```html
<!-- Не проскроллен -->
<header class="fixed top-0 z-50 w-full bg-transparent">

<!-- Проскроллен -->
<header class="fixed top-0 z-50 w-full border-b border-line/60 bg-void/80 backdrop-blur-2xl">
```

**Scroll progress bar:**
```html
<div
  class="absolute bottom-0 left-0 h-[2px] origin-left"
  style="background: linear-gradient(90deg, var(--color-neon-violet), var(--color-neon-cyan), var(--color-neon-pink))"
/>
```

---

## 7. Layout

### Контейнер

```html
<div class="mx-auto max-w-7xl px-6 lg:px-10">
```

### Секция

```html
<section class="relative py-28 md:py-36">
  <div class="mx-auto max-w-7xl px-6 lg:px-10">
    <!-- Заголовок секции -->
    <div class="mb-6 flex items-center gap-3">
      <div class="h-px w-8 bg-neon-violet"></div>
      <span class="font-display text-xs uppercase tracking-[0.2em] text-neon-violet">
        SUBTITLE
      </span>
    </div>
    <h2 class="mb-4 font-display text-3xl font-bold tracking-tight md:text-4xl">
      Title
    </h2>
    <p class="mb-14 max-w-2xl text-text-mid">Description</p>

    <!-- Контент (сетка) -->
    <div class="grid gap-5 sm:grid-cols-2">
      <!-- Карточки -->
    </div>
  </div>
</section>
```

### Section Divider

```css
.section-divider::before {
  content: "";
  position: absolute;
  left: 50%;
  top: 0;
  transform: translateX(-50%);
  width: min(80%, 600px);
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--color-line-light) 30%, var(--color-line-light) 70%, transparent);
}
```

---

## 8. Текстурные оверлеи

### Noise (зернистость)

```css
.noise::before {
  content: "";
  position: fixed;
  inset: 0;
  z-index: 50;
  pointer-events: none;
  opacity: 0.025;          /* Light: 0.01 */
  background-image: url("/noise.png");
  background-size: 128px 128px;
  background-repeat: repeat;
}
```

### Scanlines

```css
.scanlines::after {
  content: "";
  position: fixed;
  inset: 0;
  z-index: 49;
  pointer-events: none;
  background: repeating-linear-gradient(
    0deg,
    transparent,
    transparent 2px,
    rgba(0, 0, 0, 0.03) 2px,
    rgba(0, 0, 0, 0.03) 4px
  );
}
```

---

## 9. Анимации (Framer Motion)

### Stagger Container

```tsx
const stagger = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.12, delayChildren: 0.5 } },
};
```

### Fade Up

```tsx
const fadeUp = {
  hidden: { opacity: 0, y: 30 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.7, ease: "easeOut" } },
};
```

### Scroll-triggered (GlowCard)

```tsx
<motion.div
  initial={{ opacity: 0, y: 24 }}
  whileInView={{ opacity: 1, y: 0 }}
  viewport={{ once: true, margin: "-60px" }}
  transition={{ duration: 0.5, delay: 0, ease: "easeOut" }}
/>
```

### Mobile Menu Item

```tsx
<motion.a
  initial={{ opacity: 0, x: -20 }}
  animate={{ opacity: 1, x: 0 }}
  transition={{ delay: i * 0.06, duration: 0.3 }}
/>
```

### Orb Pulse (CSS)

```css
@keyframes orb-pulse {
  0%, 100% { transform: translate(-50%, -50%) scale(1); }
  50% { transform: translate(-50%, -50%) scale(1.15); }
}
```

---

## 10. Фоновые декорации

### Размытые сферы (blur blobs)

```html
<!-- Violet blob -->
<div class="absolute -left-[20%] -top-[10%] h-[600px] w-[600px] rounded-full bg-neon-violet/[0.07] blur-[120px]" />

<!-- Cyan blob -->
<div class="absolute -bottom-[10%] -right-[15%] h-[500px] w-[500px] rounded-full bg-neon-cyan/[0.05] blur-[100px]" />
```

### Dashed circles (вокруг аватара)

```html
<div class="absolute -inset-4 rounded-full border border-dashed border-line/50 opacity-60" />
<div class="absolute -inset-8 rounded-full border border-dashed border-line/30 opacity-40" />
<div class="absolute inset-0 rounded-full bg-gradient-to-br from-neon-violet/20 via-transparent to-neon-cyan/20 blur-2xl" />
```

### Online badge

```html
<div class="flex items-center gap-1.5 rounded-full border border-surface bg-surface px-2 py-0.5">
  <div class="h-1.5 w-1.5 rounded-full bg-neon-cyan animate-pulse" />
  <span class="font-display text-xs uppercase tracking-wider text-neon-cyan">Online</span>
</div>
```

---

## 11. Scrollbar

```css
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--color-void); }
::-webkit-scrollbar-thumb { background: var(--color-line); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--color-text-dim); }
```

---

## 12. Focus & Accessibility

```css
:focus-visible {
  outline: 2px solid var(--color-neon-violet);
  outline-offset: 2px;
  border-radius: 2px;
}

/* Skip to content */
.skip-to-content {
  /* скрыт по умолчанию, появляется при фокусе */
  padding: 0.75rem 1.5rem;
  background: var(--color-surface);
  border: 1px solid var(--color-neon-violet);
  color: var(--color-neon-violet);
  font-family: var(--font-display);
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

---

## 13. Градиенты

### Текстовый градиент

```html
<span class="bg-gradient-to-r from-neon-violet via-neon-blue to-neon-cyan bg-clip-text text-transparent">
  Gradient Text
</span>
```

### Scroll bar градиент

```
linear-gradient(90deg, var(--color-neon-violet), var(--color-neon-cyan), var(--color-neon-pink))
```

### Линейный разделитель

```
linear-gradient(90deg, transparent 0%, var(--color-neon-violet) 20%, var(--color-neon-cyan) 80%, transparent 100%)
```

---

## 14. Responsive breakpoints

| Breakpoint | Размер | Пример |
|-----------|--------|--------|
| По умолчанию | < 640px | Mobile first |
| `sm:` | >= 640px | 2 колонки |
| `md:` | >= 768px | Desktop nav |
| `lg:` | >= 1024px | Широкие отступы |
| `xl:` | >= 1280px | Максимальная ширина |

**Контейнер:** `max-w-7xl` (1280px)
**Паддинги:** `px-6 lg:px-10`
**Секции:** `py-28 md:py-36`

---

## 15. Быстрый старт — копипаст

Минимальный набор для нового проекта с этим дизайном:

### 1. Установить зависимости
```bash
npm install framer-motion lucide-react
```

### 2. Скопировать globals.css (секция @theme + все утилитарные классы)

### 3. Настроить шрифты в layout.tsx (Space Mono + Outfit)

### 4. Положить `/public/noise.png` (128x128 тайловая текстура шума)

### 5. Обернуть body:
```html
<body class="noise scanlines">
```

### 6. Использовать готовые классы:
- `glow-border` — карточки
- `tag-pill` — метки
- `gradient-line` — разделители
- `neon-hover` — ховер текста
- `dot-grid` — фоновая сетка
- `terminal-prompt` — терминальный промпт
- `cursor-blink` — мигающий курсор
- `section-divider` — разделитель секций
