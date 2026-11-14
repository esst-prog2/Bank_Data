# Promo page: design brief

Output of `/impeccable shape` (step 3b of the promo page homework). Planning only, no code.
Product facts live in `PRODUCT.md`; the content source is `README.md`.

## 1. Job and audience
- **Who arrives:** mostly course reviewers and classmates following a submission link, plus some analysts and researchers. They know nothing about the project yet and spend under a minute deciding whether to click through.
- **Visitor mode:** Persuade. Within seconds they need to understand what it is, why it matters, and where to click.

## 2. Outcome and proof
- **Primary action:** open the live dashboard (https://esst-prog2.github.io/Bank_Data/dashboard.html).
- **Secondary actions:** see the direct function-call snapshots (`review.html`, `compare.html`) and install the package from the GitHub repo.
- **Success:** a visitor who leaves after one screen can say "click European banks on a map, compare them, and every number traces back to its filing."
- **Real proof the page carries** (all taken from the repo, none invented):
  - The 28-bank pilot, with logos and countries.
  - Real figures from `dashboard/comparison_data.json`.
  - The Erste Group RWA disagreement: EU KM1 149.7bn vs EU OV1 147.5bn, about 1.5% apart. Both figures are shown, never merged.
  - The four real package functions the dashboard calls.
  - The scope limits: ESEF-only, course-term MVP, no hosted API.

## 3. Selected direction: Atlas Plate I
Chosen on the decision page (`seed:a2b8e26acbe32464`, re-roll 1; you picked Impeccable's pick over the assigned direction, Market Data Pages).
- **World:** the page is Plate I of a statistical atlas of European banking. It has a numbered thematic map plate, a legend box, and plate notes citing the sources.
- **Thread from the dashboard:** the dashboard's map and its green, pushed bolder. Land is shaded in graded greens from `#cdeadd` to `#0f5a3c`, on white with near-black ink.
- **Colour roles:** a single amber is reserved for source disagreement, the same as the dashboard (`#8a5a00` text, `#fff8ec` wash, `#d9a441` rule; deeper `#b07410` for the map ring). *Changed 2026-11-14 from red `#a3242b`, user decision: disagreement isn't an error, and the colour must mean the same thing on both pages.*
- **Focal moment:** the map plate fills most of the first viewport, with the 28 banks as numbered markers. The plate key (numbered bank list) and the legend sit in the plate's own margins. The primary action is set as the plate's caption line ("Open the interactive plate → dashboard") and is plainly a button.
- **Sequence below the fold:** plate notes in atlas-footnote form.
  1. What a figure is: source template, period, provenance.
  2. Where sources disagree: the Erste KM1/OV1 pair, shown as two figures.
  3. How to try it: numbered steps (open the dashboard; add up to 6 banks; pick concepts; read or export).
  4. Under the hood: the four package functions, the snapshot pages, the install link.
  5. Scope, honestly: what's covered this term and what isn't.
- **Build path:** code-led. No image tool exists here, so the ambition lives in the direction contract written at build time.

## 4. Scope and boundaries
- **Target:** a new `docs/index.html`, which becomes the site root at esst-prog2.github.io/Bank_Data/. It is one self-contained static page.
- **Untouched:** `dashboard.html`, `review.html`, `compare.html`, the package code, and the dashboard's generator scripts.
- **Anti-goals:**
  - No invented users, testimonials or adoption numbers.
  - No personal info: no author name, no email.
  - No impersonation of real institutions (ECB, EBA, bank branding beyond the logos used factually to identify the pilot banks).
  - No SaaS template look: no centred headline over three feature cards.
  - No cream-plus-serif "atlas costume".

## 5. States and ranges
- **Map plate:** exactly 28 markers. Some countries hold several banks, so marker numbering and the key must handle clusters (FR, DE, IT, ES).
- **Figures:** only real values. Missing data appears as a dash with its reason, the same convention as the dashboard.
- **Viewports:** desktop 1280–1600 wide, and phone at 390 wide. On a phone the plate stacks above the key, and the caption button stays in the first screen.

## 6. Interaction and layout
- Hovering or focusing a marker highlights its key entry, and vice versa, with the bank name and country. Keyboard and touch work the same way. This is the signature interaction.
- Everything sits on one baseline grid, and tabular figures are used throughout.
- Motion is limited to one plate reveal on load. Content stays visible if motion is off, and `prefers-reduced-motion` is respected.

## 7. Constraints and open decisions
- **Hosting:** GitHub Pages from `/docs` on `main`; the repo stays public. The page must be self-contained, with assets inlined or committed under `docs/`. The map SVG and logos can be reused from `dashboard/`.
- **Accessibility:** colour is never the only carrier of meaning (the disagreement amber also gets a label), text meets WCAG AA contrast, and the map has a text alternative (the key is a real list).
- **Open decision, yours:** should a plate-key entry open the dashboard with that bank already in the basket? The dashboard has no URL-parameter support today, so this would mean a small dashboard change. **Default: no.** Key entries just link to the dashboard, which stays untouched.
- **Fonts:** the face is chosen at build time, avoiding the training-data defaults. If it needs to stay self-contained, it's served from `docs/`.
