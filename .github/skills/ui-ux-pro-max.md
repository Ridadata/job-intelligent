# UI/UX Pro Max — Design Intelligence

Comprehensive design guide for web applications. Contains 50+ styles, 161 color palettes, 57 font pairings, 99 UX guidelines, and 25 chart types. Adapted for **React + TypeScript + TailwindCSS + Shadcn UI** stack.

---

## When to Apply

### Must Use

- Designing new pages (Landing Page, Dashboard, Admin, SaaS)
- Creating or refactoring UI components (buttons, modals, forms, tables, charts)
- Choosing color schemes, typography systems, spacing standards, or layout systems
- Reviewing UI code for user experience, accessibility, or visual consistency
- Implementing navigation structures, animations, or responsive behavior
- Making product-level design decisions (style, information hierarchy, brand expression)
- Improving perceived quality, clarity, or usability of interfaces

### Recommended

- UI looks "not professional enough" but the reason is unclear
- Receiving feedback on usability or experience
- Pre-launch UI quality optimization
- Building design systems or reusable component libraries

### Skip

- Pure backend logic development
- Only involving API or database design
- Performance optimization unrelated to the interface
- Infrastructure or DevOps work
- Non-visual scripts or automation tasks

**Decision criteria:** If the task will change how a feature looks, feels, moves, or is interacted with, this skill should be used.

---

## Rule Categories by Priority

| # | Category | Priority | Focus | Key Rules | Common Anti-Patterns |
|---|----------|----------|-------|-----------|---------------------|
| 1 | Accessibility | CRITICAL | UX | Contrast 4.5:1, Alt text, Keyboard nav, Aria-labels | Removing focus rings, Icon-only buttons without labels |
| 2 | Touch & Interaction | CRITICAL | UX | Min size 44×44px, 8px+ spacing, Loading feedback | Reliance on hover only, Instant state changes (0ms) |
| 3 | Performance | HIGH | UX | WebP/AVIF, Lazy loading, Reserve space (CLS < 0.1) | Layout thrashing, Cumulative Layout Shift |
| 4 | Style Selection | HIGH | Style | Match product type, Consistency, SVG icons (no emoji) | Mixing flat & skeuomorphic randomly, Emoji as icons |
| 5 | Layout & Responsive | HIGH | UX | Mobile-first breakpoints, Viewport meta, No horizontal scroll | Horizontal scroll, Fixed px container widths, Disable zoom |
| 6 | Typography & Color | MEDIUM | Design | Base 16px, Line-height 1.5, Semantic color tokens | Text < 12px body, Gray-on-gray, Raw hex in components |
| 7 | Animation | MEDIUM | UX | Duration 150–300ms, Motion conveys meaning, Spatial continuity | Decorative-only animation, Animating width/height, No reduced-motion |
| 8 | Forms & Feedback | MEDIUM | UX | Visible labels, Error near field, Helper text, Progressive disclosure | Placeholder-only label, Errors only at top, Overwhelm upfront |
| 9 | Navigation Patterns | HIGH | UX | Predictable back, Deep linking, Breadcrumbs for 3+ levels | Overloaded nav, Broken back behavior, No deep links |
| 10 | Charts & Data | LOW | Data | Legends, Tooltips, Accessible colors | Relying on color alone to convey meaning |

---

## Quick Reference

### 1. Accessibility (CRITICAL)

- `color-contrast` — Minimum 4.5:1 ratio for normal text (large text 3:1)
- `focus-states` — Visible focus rings on interactive elements (2–4px outline)
- `alt-text` — Descriptive alt text for meaningful images
- `aria-labels` — `aria-label` for icon-only buttons
- `keyboard-nav` — Tab order matches visual order; full keyboard support
- `form-labels` — Use `<label>` with `htmlFor` attribute
- `skip-links` — "Skip to main content" for keyboard users
- `heading-hierarchy` — Sequential h1→h6, no level skip
- `color-not-only` — Don't convey info by color alone (add icon/text)
- `reduced-motion` — Respect `prefers-reduced-motion`; reduce/disable animations when requested
- `screen-reader` — Meaningful `aria-label`/`aria-describedby`; logical reading order
- `escape-routes` — Provide cancel/back in modals and multi-step flows
- `keyboard-shortcuts` — Preserve system and a11y shortcuts; offer keyboard alternatives for drag-and-drop

### 2. Touch & Interaction (CRITICAL)

- `touch-target-size` — Min 44×44px; extend hit area beyond visual bounds if needed (use padding or pseudo-elements)
- `touch-spacing` — Minimum 8px gap between interactive targets
- `hover-vs-click` — Use click/tap for primary interactions; don't rely on hover alone
- `loading-buttons` — Disable button during async operations; show spinner or progress
- `error-feedback` — Clear error messages near the problem
- `cursor-pointer` — Add `cursor-pointer` to all clickable elements
- `tap-delay` — Use `touch-action: manipulation` to reduce 300ms delay
- `press-feedback` — Visual feedback on press (opacity change, scale, or Tailwind `active:` states)
- `gesture-alternative` — Don't rely on gesture-only interactions; always provide visible controls
- `safe-area-awareness` — Keep primary interactive elements away from screen edges
- `swipe-clarity` — Swipe actions must show clear affordance (chevron, label, hint)

### 3. Performance (HIGH)

- `image-optimization` — Use WebP/AVIF, responsive images (`srcset`/`sizes`), lazy load non-critical assets
- `image-dimension` — Declare `width`/`height` or use `aspect-ratio` to prevent layout shift (CLS)
- `font-loading` — Use `font-display: swap` or `optional` to avoid invisible text (FOIT)
- `font-preload` — Preload only critical fonts; avoid overusing preload
- `critical-css` — Prioritize above-the-fold CSS (Tailwind purges unused by default)
- `lazy-loading` — Lazy load non-hero components via `React.lazy()` + `Suspense`
- `bundle-splitting` — Split code by route/feature to reduce initial load and TTI
- `reduce-reflows` — Avoid frequent layout reads/writes; batch DOM operations
- `content-jumping` — Reserve space for async content to avoid layout jumps (CLS < 0.1)
- `virtualize-lists` — Virtualize lists with 50+ items (`@tanstack/react-virtual` or similar)
- `progressive-loading` — Use skeleton screens / shimmer instead of long blocking spinners for >1s operations
- `debounce-throttle` — Use debounce/throttle for high-frequency events (scroll, resize, input)
- `third-party-scripts` — Load third-party scripts `async`/`defer`; audit and remove unnecessary ones

### 4. Style Selection (HIGH)

- `style-match` — Match UI style to product type (SaaS → clean/minimal, Dashboard → data-dense/clear)
- `consistency` — Use same style across all pages
- `no-emoji-icons` — Use SVG icons (Lucide — already in project), not emojis
- `color-palette-from-product` — Choose palette from product/industry context
- `effects-match-style` — Shadows, blur, radius aligned with chosen style
- `state-clarity` — Make hover/pressed/disabled states visually distinct (use Tailwind `hover:`, `active:`, `disabled:`)
- `elevation-consistent` — Use a consistent shadow scale for cards, sheets, modals (Shadcn defaults)
- `dark-mode-pairing` — Design light/dark variants together using Tailwind `dark:` variant
- `icon-style-consistent` — Use one icon set (Lucide) with consistent stroke width across the product
- `primary-action` — Each screen should have only one primary CTA; secondary actions visually subordinate
- `blur-purpose` — Use blur to indicate background dismissal (modals, sheets), not as decoration

### 5. Layout & Responsive (HIGH)

- `viewport-meta` — `width=device-width, initial-scale=1` (never disable zoom)
- `mobile-first` — Design mobile-first, then scale up (Tailwind default: mobile → `sm:` → `md:` → `lg:` → `xl:`)
- `breakpoint-consistency` — Use Tailwind's systematic breakpoints: `sm` (640) / `md` (768) / `lg` (1024) / `xl` (1280) / `2xl` (1536)
- `readable-font-size` — Minimum 16px body text on mobile (avoids iOS auto-zoom on inputs)
- `line-length-control` — Mobile 35–60 chars per line; desktop 60–75 chars (`max-w-prose`)
- `horizontal-scroll` — No horizontal scroll on mobile; ensure content fits viewport width
- `spacing-scale` — Use Tailwind's 4px incremental spacing system (consistent `p-`, `m-`, `gap-` values)
- `container-width` — Consistent max-width on desktop (`max-w-6xl` / `max-w-7xl`)
- `z-index-management` — Define layered z-index scale (e.g. 0 / 10 / 20 / 40 / 50 for Shadcn overlays)
- `fixed-element-offset` — Fixed navbar/bottom bar must reserve safe padding for underlying content
- `scroll-behavior` — Avoid nested scroll regions that interfere with the main scroll experience
- `viewport-units` — Prefer `min-h-dvh` over `min-h-screen` (100vh) on mobile
- `content-priority` — Show core content first on mobile; fold or hide secondary content
- `visual-hierarchy` — Establish hierarchy via size, spacing, contrast — not color alone

### 6. Typography & Color (MEDIUM)

- `line-height` — Use `leading-relaxed` (1.625) or `leading-normal` (1.5) for body text
- `line-length` — Limit to 65–75 characters per line (`max-w-prose`)
- `font-pairing` — Match heading/body font personalities
- `font-scale` — Consistent type scale (Tailwind: `text-xs` → `text-sm` → `text-base` → `text-lg` → `text-xl` → `text-2xl` → `text-4xl`)
- `contrast-readability` — Darker text on light backgrounds (`text-slate-900` on white)
- `weight-hierarchy` — Bold headings (`font-semibold`/`font-bold`), Regular body (`font-normal`), Medium labels (`font-medium`)
- `color-semantic` — Define semantic color tokens (primary, secondary, destructive, muted) via Shadcn CSS variables, not raw hex
- `color-dark-mode` — Dark mode uses desaturated / lighter tonal variants, not inverted colors; test contrast separately
- `color-accessible-pairs` — Foreground/background pairs must meet 4.5:1 (AA) or 7:1 (AAA)
- `truncation-strategy` — Prefer wrapping over truncation; when truncating use `truncate` class and provide full text via tooltip
- `number-tabular` — Use `tabular-nums` for data columns, prices, and timers to prevent layout shift
- `whitespace-balance` — Use whitespace intentionally to group related items and separate sections

### 7. Animation (MEDIUM)

- `duration-timing` — Use 150–300ms for micro-interactions; complex transitions ≤400ms; avoid >500ms
- `transform-performance` — Use `transform`/`opacity` only; avoid animating `width`/`height`/`top`/`left`
- `loading-states` — Show skeleton or progress indicator when loading exceeds 300ms
- `excessive-motion` — Animate 1–2 key elements per view max
- `easing` — Use `ease-out` for entering, `ease-in` for exiting; avoid `linear` for UI transitions
- `motion-meaning` — Every animation must express a cause-effect relationship, not just be decorative
- `state-transition` — State changes (hover / active / expanded / collapsed / modal) should animate smoothly, not snap
- `continuity` — Page/screen transitions should maintain spatial continuity (shared element, directional slide)
- `exit-faster-than-enter` — Exit animations shorter than enter (~60–70% of enter duration) to feel responsive
- `stagger-sequence` — Stagger list/grid item entrance by 30–50ms per item; avoid all-at-once or too-slow reveals
- `interruptible` — Animations must be interruptible; user action cancels in-progress animation immediately
- `no-blocking-animation` — Never block user input during an animation; UI must stay interactive
- `scale-feedback` — Subtle scale (0.95–1.05) on press for tappable cards/buttons; restore on release
- `modal-motion` — Modals/sheets should animate from trigger source (scale+fade or slide-in) for spatial context
- `layout-shift-avoid` — Animations must not cause layout reflow or CLS; use `transform` for position changes
- `reduced-motion` — Wrap all animations in `motion-safe:` (Tailwind) or check `prefers-reduced-motion` media query

### 8. Forms & Feedback (MEDIUM)

- `input-labels` — Visible `<label>` per input (not placeholder-only)
- `error-placement` — Show error below the related field
- `submit-feedback` — Loading then success/error state on submit
- `required-indicators` — Mark required fields (e.g. asterisk)
- `empty-states` — Helpful message and action when no content
- `toast-dismiss` — Auto-dismiss toasts in 3–5s (use Shadcn `sonner` or `toast`)
- `confirmation-dialogs` — Confirm before destructive actions (use Shadcn `AlertDialog`)
- `input-helper-text` — Provide persistent helper text below complex inputs, not just placeholder
- `disabled-states` — Disabled elements use reduced opacity (`opacity-50`) + `cursor-not-allowed` + `disabled` attribute
- `progressive-disclosure` — Reveal complex options progressively; don't overwhelm users upfront
- `inline-validation` — Validate on blur (not keystroke); show error only after user finishes input
- `input-type-keyboard` — Use semantic input types (`email`, `tel`, `number`, `url`) to trigger correct mobile keyboard
- `password-toggle` — Provide show/hide toggle for password fields
- `autofill-support` — Use `autoComplete` attributes so the browser can autofill
- `undo-support` — Allow undo for destructive or bulk actions (e.g. "Undo delete" toast)
- `success-feedback` — Confirm completed actions with brief visual feedback (checkmark, toast, color flash)
- `error-recovery` — Error messages must include a clear recovery path (retry, edit, help link)
- `multi-step-progress` — Multi-step flows show step indicator or progress bar; allow back navigation
- `error-clarity` — Error messages must state cause + how to fix (not just "Invalid input")
- `field-grouping` — Group related fields logically (`fieldset`/visual grouping)
- `focus-management` — After submit error, auto-focus the first invalid field
- `destructive-emphasis` — Destructive actions use `destructive` variant (red) and are visually separated from primary actions
- `toast-accessibility` — Toasts must not steal focus; use `aria-live="polite"` for screen reader announcement
- `aria-live-errors` — Form errors use `aria-live` region or `role="alert"` to notify screen readers

### 9. Navigation Patterns (HIGH)

- `nav-limit` — Top/sidebar navigation should be concise; group secondary items in dropdowns or sub-menus
- `drawer-usage` — Use drawer/sidebar for secondary navigation, not primary actions (Shadcn `Sheet`)
- `back-behavior` — Back navigation must be predictable and consistent; preserve scroll/state
- `deep-linking` — All key screens must be reachable via URL for sharing and bookmarking (React Router)
- `nav-label-icon` — Navigation items should have both icon and text label; icon-only nav harms discoverability
- `nav-state-active` — Current location must be visually highlighted (color, weight, indicator) in navigation
- `nav-hierarchy` — Primary nav vs secondary nav must be clearly separated
- `modal-escape` — Modals and sheets must offer a clear close/dismiss affordance (Shadcn handles this)
- `search-accessible` — Search must be easily reachable; provide recent/suggested queries
- `breadcrumb-web` — Use breadcrumbs for 3+ level deep hierarchies to aid orientation
- `state-preservation` — Navigating back must restore previous scroll position, filter state, and input
- `overflow-menu` — When actions exceed available space, use overflow/more menu instead of cramming
- `adaptive-navigation` — Large screens (≥1024px) prefer sidebar; small screens use top nav or hamburger menu
- `back-stack-integrity` — Never silently reset the navigation stack or unexpectedly jump to home
- `navigation-consistency` — Navigation placement must stay the same across all pages
- `focus-on-route-change` — After page transition, move focus to main content region for screen reader users
- `persistent-nav` — Core navigation must remain reachable from deep pages; don't hide it entirely in sub-flows
- `destructive-nav-separation` — Dangerous actions (delete account, logout) must be visually and spatially separated from normal nav items

### 10. Charts & Data (LOW)

- `chart-type` — Match chart type to data type (trend → line, comparison → bar, proportion → pie/donut)
- `color-guidance` — Use accessible color palettes; avoid red/green only pairs for colorblind users
- `data-table` — Provide table alternative for accessibility; charts alone are not screen-reader friendly
- `pattern-texture` — Supplement color with patterns or shapes so data is distinguishable without color
- `legend-visible` — Always show legend; position near the chart, not detached below a scroll fold
- `tooltip-on-interact` — Provide tooltips/data labels on hover showing exact values
- `axis-labels` — Label axes with units and readable scale; avoid truncated labels on mobile
- `responsive-chart` — Charts must reflow or simplify on small screens (horizontal bar instead of vertical, fewer ticks)
- `empty-data-state` — Show meaningful empty state when no data exists ("No data yet" + guidance), not a blank chart
- `loading-chart` — Use skeleton or shimmer placeholder while chart data loads
- `animation-optional` — Chart entrance animations must respect `prefers-reduced-motion`; data should be readable immediately
- `large-dataset` — For 1000+ data points, aggregate or sample; provide drill-down for detail
- `number-formatting` — Use locale-aware formatting for numbers, dates, currencies on axes and labels
- `no-pie-overuse` — Avoid pie/donut for >5 categories; switch to bar chart for clarity
- `contrast-data` — Data lines/bars vs background ≥3:1; data text labels ≥4.5:1
- `legend-interactive` — Legends should be clickable to toggle series visibility
- `sortable-table` — Data tables must support sorting with `aria-sort` indicating current sort state
- `error-state-chart` — Data load failure must show error message with retry action, not a broken/empty chart

---

## Common Anti-Patterns

| Anti-Pattern | Why It's Bad | Fix |
|---|---|---|
| Emoji as structural icons (🎨 🚀 ⚙️) | Font-dependent, inconsistent cross-platform, no design token control | Use Lucide SVG icons |
| Placeholder-only labels | Disappear on input, fail accessibility, confuse users | Always use visible `<label>` elements |
| Hover-only interactions | Unusable on touch devices, excludes mobile users | Use click/tap as primary; hover as enhancement only |
| Mixing flat & skeuomorphic styles | Breaks visual consistency, looks unfinished | Pick one style and apply across all pages |
| Raw hex colors in components | Impossible to theme, breaks dark mode, hard to maintain | Use Shadcn CSS variables / Tailwind semantic classes |
| Animating width/height/top/left | Causes layout reflow, janky performance | Use `transform` and `opacity` only |
| Gray-on-gray text | Fails contrast requirements, hard to read | Ensure 4.5:1 minimum contrast ratio |
| `100vh` on mobile | Doesn't account for browser chrome, content hidden | Use `min-h-dvh` or `min-h-screen` with caution |
| Errors shown only at form top | User can't find which field is wrong | Show error directly below the relevant field |
| No loading/empty/error states | Looks broken when data is unavailable | Every page must handle: loading (skeleton), error (boundary), empty (message + action) |
| Icon-only buttons without labels | Screen readers can't announce purpose, low discoverability | Add `aria-label` or visible text label |
| Disabling zoom via viewport meta | Fails WCAG, harms low-vision users | Never set `maximum-scale=1` or `user-scalable=no` |
| Layout shift from async content | Poor CLS score, jarring user experience | Reserve space with `aspect-ratio` or fixed dimensions |

---

## Pre-Delivery Checklist

### Visual Quality
- [ ] No emojis used as icons (use Lucide SVG instead)
- [ ] All icons from Lucide with consistent size and stroke width
- [ ] Semantic Shadcn/Tailwind color tokens used consistently (no hardcoded hex)
- [ ] Pressed/hover state visuals do not shift layout bounds

### Interaction
- [ ] All clickable elements have `cursor-pointer` and visible feedback on interaction
- [ ] Touch targets meet minimum size (≥44×44px)
- [ ] Micro-interaction timing stays in 150–300ms range
- [ ] Disabled states are visually clear and non-interactive (`opacity-50` + `cursor-not-allowed`)
- [ ] Screen reader focus order matches visual order; interactive elements have labels

### Light/Dark Mode
- [ ] Primary text contrast ≥4.5:1 in both light and dark mode
- [ ] Secondary text contrast ≥3:1 in both light and dark mode
- [ ] Dividers/borders and interaction states are distinguishable in both modes
- [ ] Both themes tested before delivery (use Tailwind `dark:` variant)

### Layout
- [ ] No horizontal scroll on any viewport width
- [ ] Verified on 375px (small phone), 768px (tablet), and 1440px (desktop)
- [ ] Tailwind spacing scale (4/8px rhythm) maintained across components
- [ ] Fixed navbar/footer reserves proper padding for content underneath
- [ ] Long-form text uses `max-w-prose` for readable line length

### Accessibility
- [ ] All meaningful images/icons have `alt` text or `aria-label`
- [ ] Form fields have visible labels, helper text, and clear error messages
- [ ] Color is not the sole indicator of state or meaning
- [ ] `prefers-reduced-motion` is respected (use `motion-safe:` in Tailwind)
- [ ] Heading hierarchy is sequential (h1→h2→h3, no level skip)
- [ ] Skip-to-content link present for keyboard users

### Performance
- [ ] Images use `loading="lazy"` for below-the-fold content
- [ ] Lists with 50+ items are virtualized
- [ ] Route-level code splitting via `React.lazy()` + `Suspense`
- [ ] Skeleton loaders shown for async content (no blank screens)
- [ ] `debounce` applied to search/filter inputs
