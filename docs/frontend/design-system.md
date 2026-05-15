# Design System

Archived experimental design-system notes for the recruitment matching product.
These notes are not source of truth for the next frontend implementation.

## Intent

- Search-first workflow
- Dense but scannable enterprise UI
- AI-assisted actions without turning the interface into a dashboard of gimmicks
- Shared shell for recruiter and candidate modes
- Desktop-first, responsive without collapsing the information hierarchy

## Visual Direction

Avoid generic white-plus-purple SaaS styling. The product should feel operational, sharp, and credible.

- Brand mood: cobalt, ink, mist, and emerald accents
- Primary surfaces: light neutral, low-noise
- AI accents: restrained, used only where the system is reasoning or ranking
- Typography: practical and modern, not default browser/system fallback

## Tokens

### Color

```css
:root {
  --bg-page: #f3f6fb;
  --bg-panel: #ffffff;
  --bg-subtle: #eef3f8;
  --bg-hover: #e8eef7;

  --text-strong: #122033;
  --text-body: #405166;
  --text-muted: #6f8196;
  --text-inverse: #ffffff;

  --border-soft: #dbe4ee;
  --border-strong: #b8c6d8;
  --border-focus: #0f5bd3;

  --brand-primary: #0f5bd3;
  --brand-primary-hover: #0b49ab;
  --brand-soft: #dce9ff;

  --accent-emerald: #0f9f6e;
  --accent-amber: #dd8a13;
  --accent-red: #d64545;
  --accent-cyan: #1286a8;

  --ai-bg: #e8f7f6;
  --ai-border: #9ed9d5;
  --ai-text: #0c6b67;

  --match-high: #11885c;
  --match-medium: #d58a1d;
  --match-low: #7e8a98;
}
```

### Typography

```css
:root {
  --font-heading: "Manrope", "Segoe UI", sans-serif;
  --font-body: "IBM Plex Sans", "Segoe UI", sans-serif;
  --font-mono: "JetBrains Mono", monospace;
}
```

Recommended scale:

- Page title: `28/34`, semibold
- Section title: `20/28`, semibold
- Card title: `16/24`, semibold
- Body: `14/22`, regular
- Dense metadata: `12/18`, medium
- Table header / badge label: `11/16`, semibold, slight letter spacing

### Spacing

Use a 4px base scale.

- `4, 8, 12, 16, 20, 24, 32, 40, 48, 64, 80`
- Dense UI defaults:
  - panel padding `20-24`
  - card gap `12-16`
  - section gap `32`
  - table cell padding `12`

### Radius and Shadow

```css
:root {
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 14px;
  --radius-xl: 18px;

  --shadow-sm: 0 1px 2px rgba(18, 32, 51, 0.06);
  --shadow-md: 0 8px 20px rgba(18, 32, 51, 0.08);
  --shadow-lg: 0 20px 40px rgba(18, 32, 51, 0.12);
  --shadow-focus: 0 0 0 3px rgba(15, 91, 211, 0.18);
}
```

## Layout Patterns

### Shared App Shell

- Top header: logo, mode switch, primary nav, user menu
- Optional left navigation on larger screens when library-heavy flows are active
- Content max width: `1280-1440px`

### Library Pages

- Header row with title, count, and primary CTA
- Search mode switch directly below header
- Left filters column `280-320px`
- Main result region with list-first view

### Detail Pages

- Two-column layout:
  - main narrative/data column
  - sticky action column
- Job and CV detail share one skeleton, only field groups differ

### Matching Workspace

- Three-column layout is canonical:
  - anchor list
  - selected anchor preview + controls
  - ranked results
- Do not fragment this screen into smaller pages in V1 wireframe

## Core Components

### Buttons

- Primary: brand fill, white text
- Secondary: subtle fill, strong text
- Tertiary: text-only or ghost
- Destructive: red accent only for irreversible actions

### Search Inputs

Two distinct search patterns must exist:

- Exact search:
  - entity-aware fields like title, name, email
  - form-like, filter-oriented
- Semantic search:
  - natural language prompt
  - score-based result framing
  - visible AI/semantic indicator

Do not merge both modes into one ambiguous search box.

### Cards

- Result cards are compact, comparable, and action-oriented
- Key structure:
  - primary title
  - metadata row
  - tags
  - score or status
  - quick actions

### Data Tables

Use tables only where batch comparison matters:

- shortlist management
- recent runs/history
- admin-like libraries if density becomes more important than scanning cards

### Tags and Badges

- Skills: neutral filled pills
- Status: neutral or semantic outline badges
- Match scores: color-coded with numeric label, never color-only

### Empty and Error States

Every major flow needs explicit UI for:

- empty library
- no exact results
- no semantic results
- no matches above threshold
- extraction failure
- item not found
- session expired

## AI-Specific Patterns

### Match Score

- Show numeric score plus label, not just a progress bar
- Keep score language consistent:
  - `Strong`
  - `Qualified`
  - `Borderline`

### Reasoning Panel

- Use short evidence bullets
- Separate deterministic facts from generated interpretation
- Example structure:
  - `Skills overlap: 7/9`
  - `Seniority: exact match`
  - `Missing required certification`

### Extraction Review

This is a first-class product screen, not a hidden modal.

- Left: raw extracted text preview
- Right: normalized fields
- Warnings for low confidence, noise, missing required metadata
- Actions:
  - confirm and save
  - edit fields
  - re-upload

## Responsive Rules

- Desktop is the primary design target
- Tablet:
  - collapse side panels into drawers
  - keep matching results readable without losing controls
- Mobile:
  - support review tasks, not heavy authoring
  - allow upload status, detail reading, shortlist viewing, and lightweight search refinement

## Accessibility

- Visible focus ring on all actionable elements
- Minimum text contrast WCAG AA
- Do not communicate score, status, or validation with color alone
- Keyboard access for search mode switching, result selection, dialogs, and upload flows

## Implementation Notes

- Current repo has no active frontend runtime; future UI should be redesigned
  before implementation.
- When coding against the MVP, map tokens into one shared CSS variable file first.
- Backend/API documentation should stay in backend docs and OpenAPI, not duplicated here unless the UI contract depends on it.
