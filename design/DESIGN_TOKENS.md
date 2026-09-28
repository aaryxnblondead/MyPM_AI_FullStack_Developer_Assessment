# Design tokens from talentstack.in CSS

Source: `design/css/*.css`, 36 files. Parsed by `scripts/extract_tokens.py` plus manual read. Raw counts in `design/design-tokens.json`. No invented values.

## 1. File inventory

| File | Size | What it holds |
|---|---|---|
| about.css | 10.5 KB | About sections, image blocks, experience badge |
| animate.css | 82.2 KB | Generic keyframe animation library |
| banner.css | 16.4 KB | Hero banner styles, carousel text |
| bootstrap.css | 232.3 KB | Framework defaults, not brand. Used only for grid and reset reference |
| category.css | 1.7 KB | Category chips |
| chooseus.css | 5.5 KB | Why choose us blocks with icon boxes |
| clients.css | 2.7 KB | Client logo row |
| color.css | 7.7 KB | Theme color mappings using vars, no new hex |
| contact.css | 3.9 KB | Contact info boxes and form spacing |
| css2.css | 0.8 KB | Outfit font-face latin plus latin-ext, weights 100 to 900 |
| css2 (1).css | 3.3 KB | Inter font-face subsets, weights 100 to 900 |
| elpath.css | 52.8 KB | Icon path helpers, decorative shapes |
| flaticon.css | 2.6 KB | Flaticon font-face plus icon classes |
| font-awesome-all.css | 97 KB | Icon font plus utilities, not brand color |
| footer.css | 4.6 KB | Footer links and social row |
| funfact.css | 1.1 KB | Counter stats row |
| header.css | 17.9 KB | Sticky header, nav, menu right content |
| industries.css | 7.7 KB | Industry cards with icon boxes |
| job.css | 8.1 KB | Job form, job cards, filter pills. Key source for forms and cards |
| jquery.fancybox.min.css | 13.4 KB | Lightbox vendor styles |
| login.css | 3.6 KB | Sign in form box |
| news.css | 8.5 KB | Blog cards and sidebar |
| nice-select.css | 3 KB | Custom select dropdown |
| odometer.css | 3 KB | Number counter |
| owl.css | 5.3 KB | Carousel vendor styles |
| page-title.css | 1.1 KB | Page hero title band |
| portfolio.css | 4.3 KB | Portfolio grid and filter tabs |
| process.css | 8.2 KB | Process steps with count badge |
| responsive.css | 2.3 KB | Breakpoint overrides only |
| rtl.css | 2.1 KB | Right to left overrides |
| service.css | 2.5 KB | Service cards |
| service-details.css | 5.3 KB | Service detail plus sidebar |
| style.css | 35.8 KB | Brand root, base type, buttons, forms. Primary source |
| subscribe.css | 4.2 KB | Newsletter band |
| team.css | 2.5 KB | Team cards |
| testimonial.css | 9.2 KB | Quote cards |

Brand truth lives in `style.css:71-78`, `color.css`, `job.css:1-130`, `header.css:1-80`. Bootstrap and vendor files are not brand.

## 2. Colors

Root in `style.css:71-78`:
- `--theme-color: #666666`
- `--theme-color-2: #113754`
- `--secondary-color: #666666`
- `--text-color: #666666`
- `--title-color: #111111`
- body bg `#ffffff` in `style.css:91-97`

Top non bootstrap counts from extractor:
- `#ffffff` 253 refs, first `about.css:31`, role background and surface
- `#113754` 15 refs, first `color.css:212`, role primary. Used for `.theme-btn` bg in `style.css:391-407` and job icon boxes in `job.css:43`
- `#eff2e6` 11 refs, first `about.css:404`, role tinted section bg
- `#666666` 8 refs, first `about.css:302`, role secondary text and hover bg
- `#e5e5e5` 18 refs, first `job.css:80`, role border and divider
- `#e3e7eb` in `style.css:1132`, role mist fill
- `#141417` in `style.css:1320`, role ink text alt
- `#111111` in `style.css:76`, role heading. `.theme-btn.btn-two` uses `#111111` in `style.css:418-420`
- `#808080` in `style.css:1307`, role muted
- `#dddddd` in `job.css` borders, role border alt

Semantic mapping used in code:
- primary: #113754
- secondary: #666666
- accent: #666666 (same as secondary in source, kept as is)
- background: #ffffff
- surface: #ffffff
- tint: #eff2e6
- mist: #e3e7eb
- text body: #666666
- text title: #111111
- text ink: #141417
- muted: #808080
- border: #e5e5e5
- success, warning, danger: not defined in brand CSS. Bootstrap defines `#198754`, `#ffc107`, `#dc3545` but those are framework defaults. Gap noted below. UI uses muted red and green only for errors and status, flagged for approval.

## 3. Typography

Families in exact order:
- text: `"Inter", sans-serif` in `style.css:77`
- title: `"Outfit", sans-serif` in `style.css:78`
- icon: `'icomoon'` 8 uses, `'Font Awesome 5 Pro'` 8 uses, `'Flaticon'` via `flaticon.css:1`
- mono: bootstrap `--bs-font-monospace`, no brand mono

Faces:
- Outfit 100 to 900, swap, remote woff2 in `css2.css:2-19`
- Inter 100 to 900, swap, remote woff2 subsets in `css2 (1).css:2-80`
- No local font files in `design/css/`. Gap noted.

Weights in use: 400 body in `style.css:91-97`, 500 buttons in `style.css:391-407`, 600 headings implied by banner and title blocks.
Scale observed: 12, 14, 16 base, 18, 20, 24, 30 to 40 for headings. Base 16px line 26px in `style.css:91-97`.
Headings use title font. Body uses text font. No letter spacing token found. Uppercase used sparingly for labels and tabs.

## 4. Spacing and layout

- Container 1200px max with 15px sides in `style.css:98-103`
- Large container 1680px in `style.css:105-109`
- Gutter 30px via `--bs-gutter-x` in `style.css:377`
- Job input height 60px, padding 10px 25px in `job.css:70-82`
- Textarea height 150px, radius 20px in `job.css:100-107`
- Button padding 15px 40px in `style.css:391-407`
- Section rhythm uses 80 to 134px top offsets in job and banner files
- Base unit reads as 5px with steps 5, 10, 15, 20, 25, 30, 40. Pill radius 50px is separate.

## 5. Radii, borders, shadows, motion, z, breakpoints

- Radius: 50 percent round icons 65 uses, 10px cards 47 uses, 50px pills 6 uses in `style.css:403` and `job.css:81`, 40px inputs in `job.css:81`, 20px textarea in `job.css:100`, 5px small in `style.css:787`. Cards use 10px. See `job.css:19-20` and `job.css:135-136`.
- Borders: 1px solid #e5e5e5 for cards and inputs. See `job.css:80` and `job.css:145`.
- Shadows: mostly none. Decorative ring uses inset 0 0 0 2px rgba(0,46,65,0.2) in `style.css:543`. Pulse rings use white alpha shadows in `style.css:604-619`. No card drop shadow token in brand. Cards rely on border, not shadow.
- Transitions: `all 0.5s ease-in-out` for buttons in `style.css:391-407`, `all 500ms ease` for inputs in `job.css:70-82`.
- z-index: 1 for buttons in `style.css:391-407`. Header sticky uses default stacking. No scale token found.
- Breakpoints: 1799, 1499, 1399, 1299, 1200, 991, 767, 599, 499 in `responsive.css:4-151` plus 1200 min in `style.css:98`. Key steps for UI: 1200, 991, 767, 599, 499.

## 6. Buttons

Source `style.css:391-453`:
- `.theme-btn`: bg #113754 important, color #fff important, font Outfit 16px line 30px weight 500, radius 50px, padding 15px 40px, z 1, transition 0.5s. Hover bg secondary #666666.
- `.theme-btn.btn-two`: bg #111111 in `style.css:418-420`.
- Full width variant in job form: `.job-form-section .form-inner .theme-btn { width: 100% }` in `job.css:122-124`.
- Before and after wipe layers in `style.css:422-453` create slide fill on hover.
- Disabled state: not defined in brand CSS. Gap.
- Focus ring: not defined. Uses browser default. Gap.
- Ghost and link variants: not defined as buttons. Links use title color with hover to theme color. See `header.css:59-72`.

Mapped variants for UI: primary navy, dark, full width submit. Ghost and danger are gaps and use border only until approved.

## 7. Forms

Source `job.css:66-107`, `style.css:150-189`:
- Text, email, select height 60px, border 1px #e5e5e5, radius 40px, padding 10px 25px, font 16px, color text #666666, transition 500ms.
- Textarea height 150px, radius 20px, no resize, padding top 15px.
- Select uses nice-select custom list in `style.css:928-956` and `nice-select.css`.
- Label: no explicit label token. Uses title font small semibold by context. Gap, we use 14px semibold title color.
- Placeholder: webkit, moz, ms rules exist in `style.css:157-165` but set no color token. Gap, we use muted #808080.
- Focus: empty rule in `job.css:92-95`. Gap, we use border navy plus 2px ring rgba(17,55,84,0.2) to match inset ring feel. Flagged for approval.
- Error: no brand error token. `color.css` maps danger borders to theme color, not red. Gap, we use muted red text only for form errors until approved.

## 8. Other patterns

- Header: white bg in `header.css:24`, nav links title color with theme hover in `header.css:51-72`.
- Job card: white bg, 10px radius in `job.css:135-136`, upper box divider 1px #e5e5e5 in `job.css:145`, icon circle 50 percent navy bg in `job.css:42-43`.
- Filter pill: border 1px #e5e5e5, radius 40px in `job.css:80-81`.
- Section bands: white default, sage #eff2e6 tint blocks in `about.css:404`, mist #e3e7eb fills.
- Dividers: 1px #e5e5e5 vertical in `job.css:114-121`.
- Badges: no badge token. Gap, we use pill 50px with tint and navy text.
- Dark section: `.theme-btn.btn-two` on #111111 implies dark bands use near black. No full dark section token.

## 9. Design language

Corporate hiring site with calm navy and gray, generous white space, pill actions, soft 10px cards with hairline borders instead of shadows, Inter body copy with Outfit headings, 60px pill inputs, section bands alternating white and pale sage. Motion is slow 500ms fades and wipe fills, not springy. Breakpoints step down from 1200 to 499 with stacked layouts on mobile.

## 10. Conflicts and gaps needing your answer

1. Two theme vars both gray: `--theme-color` and `--secondary-color` are both #666666. Resolved as secondary and accent both gray, primary is navy #113754 by usage. Confirm.
2. Success, warning, danger, focus ring, disabled, placeholder color, label style, badge: not in brand CSS. Current UI uses minimal grays plus muted status colors only where needed. Approve or supply values.
3. No local font files in `design/css/`. Only remote Google woff2 URLs. We load Inter plus Outfit via `next/font/google` with exact source stacks as fallback. Approve.
4. Bootstrap hex values dominate raw counts but are framework defaults. Excluded from brand mapping. Confirm exclusion.
5. Shadows: brand uses borders, not elevation. UI cards use border only. Confirm no shadow.
6. Exact heading sizes vary by section with no single h1 to h6 scale. UI uses 30px page, 20 to 24px card, 16px body, 14px label. Confirm.
