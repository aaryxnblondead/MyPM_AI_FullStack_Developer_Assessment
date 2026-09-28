# Brand tokens parsed from talentstack.in

Source: `design/css/*.css` (copied from `references/designrefs/`). Only source used. No guessing.

## Core colors from `style.css` :root

- theme: #666666 (`--theme-color`, also secondary and text)
- theme-2 / primary navy: #113754 (`--theme-color-2`)
- text: #666666 (`--text-color`)
- title / near black: #111111 (`--title-color`)
- background: #ffffff
- support sage tint: #EFF2E6 (section backgrounds)
- support gray blue: #E3E7EB (borders and fills)
- ink: #141417 (body copy alt)
- border light: #E5E5E5
- muted: #808080

Use primary navy #113754 for buttons and key actions. Use #666666 for secondary text and accents. Use #111111 for headings. Keep backgrounds white with sage and gray blue for sections.

## Fonts

- text: Inter, sans-serif (`--text-font`)
- title: Outfit, sans-serif (`--title-font`)
- body size 16px, line height 26px, weight 400

Frontend loads Inter for body and Outfit for headings. No other families for UI.

## Shape and buttons

- pill buttons: 50px radius (`.theme-btn`)
- cards and inputs: 5px radius
- icon buttons: 50 percent round
- container max 1200px, large container 1680px

Keep buttons pill shaped, cards slightly rounded, layout centered max 1200px.

## Rules

- Do not invent new brand colors.
- If a token is missing, ask or state the gap.
- Talentstack CSS is for look only. Copy in UI stays human and direct with no em dashes.
