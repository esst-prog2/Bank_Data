# Process log — promo page homework

One row per homework step: the step, what the tool did, and what the user decided.
Append only — never rewrite an earlier row (same convention as `PLANNING_LOG.md`).

- **Step 1 (2026-11-13)** — Told Claude to commit after each step from now on and log
  it here (step / what the tool did / what was decided). Tool: none yet, this is the
  standing instruction itself. Decided: adopt it for the rest of this homework.
- **Step 3 setup (2026-11-13)** — Installed the Impeccable design skill. `/plugin
  marketplace add` isn't available in this VSCode-extension environment, so used the
  CLI path instead: `npx impeccable install`, run in the project root. It detected
  Claude Code, installed skills/agents/hooks under `.claude/` (project-local), and
  placed its engine binary under `.claude/skills/impeccable/scripts/bin/`. Decided:
  install project-local (its own default). Still pending: `/impeccable init` — the
  skill only becomes callable after this session restarts and reloads the skill list.
  The install itself (24 MB: a Windows engine binary, font index, browser-automation
  JS) is third-party tooling, not project content, so added it to `.gitignore` instead
  of committing it — same treatment as `node_modules/`.
- **Step 2 (2026-11-14)** — Never run. The homework's `/office-hours`/gstack step for
  drafting promo-page content was skipped — no draft exists anywhere in the repo or
  chat history. Decided: don't backfill it; let `/impeccable shape` build the design
  brief straight from README.md instead, as it already offered to do.
- **Step 3a — `/impeccable init` (2026-11-14)** — Skill wasn't in this session's
  skill list (session started outside the repo), so Claude followed
  `.claude/skills/impeccable/SKILL.md` and `reference/init.md` directly. Ran the
  engine's `context` check (reported no PRODUCT.md, no design context), scanned
  README/pyproject/dashboard inputs, then asked 3 interview questions. Wrote
  `PRODUCT.md` (product truth only, no visual decisions). No image-generation
  tool available, so build path is code-first by default (nothing stored); live
  mode config deferred until `generate` needs it. Decided: primary users are
  analysts & researchers; positioning leads with the dashboard (provenance is
  supporting); status framed as a course-term MVP.
- **Step 3b — `/impeccable shape` (2026-11-14)** — Content source: README.md (user
  decision; no separate step-2 draft in the repo). Claude ran a 3-question discovery
  round, then Impeccable's `concept-seed` direction roll and served its decision page
  locally. First hand (assigned: Annual Report Highlights; pick: Auditor's Working
  Paper; 6 catalog challengers, all declined) — user re-rolled. Second hand
  (assigned: Market Data Pages; pick: Atlas Plate I; one competitive challenger,
  Monochrome Product Marketing) — user chose **Atlas Plate I**. Code-led build (no
  image-generation tool here). Wrote `PROMO_BRIEF.md` (no code). Decided: primary
  action is opening the dashboard; look is "related to the dashboard but bolder";
  page lives at `docs/index.html`. Open: whether plate-key entries should deep-link
  into the dashboard with a bank preselected (needs a dashboard change; default no).
- **Step 3c — first build of `docs/index.html` (2026-11-14)** — Built from
  `PROMO_BRIEF.md` (direction "Atlas Plate I"), code-led. Claude wrote the direction
  contract to `.impeccable/surfaces/docs-index-html.md`, then built one self-contained
  static page: the slimmed dashboard map (336 KB inline SVG, from
  `dashboard/europe_map.svg`) with the 28 pilot banks as numbered markers, a key whose
  entries are plain links to the dashboard, a legend, the Erste KM1/OV1 callout, and five
  plate notes (provenance, disagreement, how to try it, the package, scope). Real
  figures only, from `dashboard/comparison_data.json` / `total_assets.json`. Self-hosted
  Archivo font (OFL, `docs/fonts/`); three real dashboard screenshots taken with
  Playwright (`docs/img/`, origin embedded in each PNG). Checked at 1600/1440/1280/1100/390
  px wide; side-panel layout from 1280 px up, stacked below. Impeccable's detector
  findings: sub-11px labels fixed; key-row "cramped padding" and the neatline-stripe
  advisory left as intentional. A one-off scratch script assembled the first version;
  `docs/index.html` is now the source file. Decided (user): no deep-linking from the key;
  build first, then `generate`. Not yet done: finish review and DESIGN.md (deferred
  until `generate`/`critique` settle the design); nothing pushed.
- **Step 3d — disagreement colour: red → amber (2026-11-14)** — User decision: use
  the dashboard's amber, not red. Reason (user's): the disagreement isn't an error but the
  provenance design working, and the colour must mean the same thing on the promo page
  and in the dashboard it hands visitors to. Claude switched the callout, the ringed
  markers, the legend swatch, the status line and Note 2's figures to the dashboard's
  values (`#8a5a00` text, `#fff8ec` wash, `#d9a441` rule; deeper `#b07410` for the
  map ring so it holds on green land), rewrote Note 2's sentence, and updated
  `PROMO_BRIEF.md` and the surface brief to match.
- **Step 3e — `/impeccable generate` on the map/key (2026-11-14)** — Claude set up
  Impeccable's live mode (`.impeccable/live/config.json`: page `docs/index.html`, no
  CSP), served `docs/` locally and opened it in the system browser (the engine assumed a
  built-in browser pane this VS Code session doesn't have). User chose direction
  **Layout** and scope **map + key + legend** (headline panel fixed). Three variants, each
  on a different axis: (1) key as a gazetteer strip under the plate; (2) legend merged into
  the key as tinted country chips, disagreement callout docked under Austria; (3) the
  disagreement promoted to an atlas-style "Inset: Austria" with both banks' KM1/OV1 pairs.
  User accepted **variant 3** at default settings. Claude then made it permanent (CSS moved
  into the page stylesheet, preview wrappers removed, framing script now places the inset
  and its dashed leader), closed the session, and fixed what the check found: the inset
  covered Ireland's and Denmark's markers (shortened it, clamped its right edge) and
  phone styles flattened the inset's markers (scoped the rule). Verified at
  1920/1600/1440/1280/1100/390 px: no markers under the inset, no horizontal scroll, no
  script errors.
- **Step 3f — `/impeccable critique` (2026-11-14)** — Run as Impeccable requires:
  two isolated sub-agents (A: design review read as a classmate, a teacher and a
  stranger, plus a mobile user; B: the detector, the detect.js overlay in headless
  Chromium, contrast, tap targets, overflow), then merged. Score **22/32** (heuristics
  7 and 10 n/a; "Acceptable", 69%). Found: **P0**: at ≥1280px the map SVG sits on top of
  the hook panel, so "Open the interactive plate" and its links can't be clicked with a
  mouse (keyboard works, which is why earlier checks missed it; caught by B). **P1**: the
  28 key entries look like per-bank links but all open the same empty dashboard; the
  main button is named in metaphor ("plate"). **P2**: cold handoff into the dashboard;
  phone map loses marker numbers. Detector false positives confirmed: key-row "cramped
  padding" (hairline separators) and the striped neatline (deliberate). Teacher-lens
  catch: `PROMO_BRIEF.md` had the KM1/OV1 figures reversed (page itself correct).
  **Single weakest part: the route from the first screen into the dashboard.**
  Snapshot kept locally in `.impeccable/critique/` (git-ignored by Impeccable).
- **Step 3g — critique fixes (2026-11-14)** — User chose: fix the P0 and the key-link P1,
  but keep the button label "Open the interactive plate" (the metaphor stays), and
  correct the brief. Claude: (1) layered the hook panel, legend, inset and key above the
  map at ≥1280px, so mouse clicks reach the button and links again (verified with
  Playwright click checks at 1920/1440/1280/1100/390); (2) turned the 28 key entries into
  plain labels that still highlight their marker on hover (the button is now the one way
  into the dashboard), and rewrote the key's idle line to say how to compare banks;
  (3) corrected `PROMO_BRIEF.md`'s Erste figures to OV1 149.7bn / KM1 147.5bn.
- **Step 3h — Impeccable finish review (2026-11-14)** — The review deferred since the
  first build. Run by a fresh sub-agent following Impeccable's shipped finish-reviewer
  definition: the `impeccable-finish-reviewer` agent type isn't loaded in this session,
  which started outside the repo, so a general-purpose agent read the definition as its
  instructions. Round 1: **recapture**. My phone screenshot had blank frames because
  lazy-loaded images never loaded; this was a capture-script bug, not a page bug. Round
  2: **fix**, with 3 material fixes: (1) the P1 change had removed keyboard access to the
  key, so entries are now focusable labels again (still not links) and focus highlights
  the marker and updates the status line; (2) at 1280x800 the plate overflowed the
  screen, so the height floor was lowered and the key/panels tightened on short screens;
  (3) the contract's "map lettering" was missing, so sea names were added in the wide
  tracked caps (Atlantic Ocean, Baltic, Mediterranean Sea; North Sea dropped because the
  inset's leader crosses that water at laptop widths). Round 3 (verdict pass): all three
  **resolved**, disposition **ship**. Also tightened the key's focus-ring offset. Noted,
  not done: "BALTIC" starts on Sweden's coast at 1280; deferred P2s (phone map, handoff
  line).
- **Step 3i — DESIGN.md (2026-11-14)** — Deferred until the design settled. Written by a
  fresh sub-agent following Impeccable's shipped documenter definition (same agent-type
  workaround as the finish review): `DESIGN.md` (colour, type, spacing tokens plus
  named rules, components, layout, motion, do's and don'ts) and the
  `.impeccable/design.json` sidecar. It records the system as built: plate green; four
  land tints; amber only for disagreement ("The One Meaning Rule"); Archivo only, with
  width as the second voice; tabular figures; hairlines rather than shadows. The
  dashboard's older look is explicitly outside this system. Drift noted, not fixed: a
  few colours are hard-coded rather than tokens, and the contract's darkest land tint
  differs from the build (documented as built). Decided (user, earlier): don't hold
  DESIGN.md back any longer.
- **Step 4–5 — publish and push (2026-11-14)** — `docs/index.html` is the GitHub Pages
  site root (Pages: `main`, `/docs`; repo public). Pushed all local commits to
  `origin/main`.
- **Step 6 — `/impeccable polish` (2026-11-14)** — Final quality pass on `docs/index.html`
  covering the deferred items (the earlier critique snapshot no longer matched the page,
  so this was an independent pass). (1) A one-sentence line under the main button says
  what the dashboard shows ("pick up to six banks on its map, choose what to compare,
  and read a table where every figure names its source"); short screens get a tighter
  version so it fits at 1366x768 and 1280x720. (2) Phone map: instead of anonymous dots,
  each country gets one tappable count badge (amber ring for Austria), about 31px tap
  area. A tap lists that country's banks by number and name in a status line under the
  map and lights them in the key; Austria adds the disagreement note. Tablets and up keep
  the numbered markers. (3) "BALTIC" moved to the southern Baltic, with a smaller and
  tighter label, after testing a grid of positions in the browser: zero land contact at
  1280/1366/1440/1920. Also: legend swatch border now uses the hairline token; DESIGN.md
  and its sidecar updated to describe the phone badges and the context line. Left as
  noted exceptions: the detector's new DESIGN.md checks flag type sizes that the DESIGN.md
  ramp doesn't list (12/15/16/19px and a 40px short-screen headline cap; the 5.2px is SVG
  map units, a false positive) and the one-off code-block background. Dashboard
  untouched. Verified: button clickable, no horizontal scroll, no script errors and keyboard
  focus into the key at 1920/1440/1280/1100/390; phone taps tested with touch emulation.
- **Step 7 — DESIGN.md token gaps (2026-11-14)** — User asked to record the values the
  detector found on the page but not in the design record (real, just undocumented), and
  to ignore the 5.2px flag (SVG map units, a false positive). Claude added to
  `DESIGN.md`'s frontmatter and prose, and to the `.impeccable/design.json` sidecar:
  type roles `display-short` (the headline's 40px cap on short wide screens), `step-title`
  (19px), `body-phone` (16px), `table` (15px: note 1's table and note 2's bank heads),
  `caption` (12px: inset caption, short-screen status line); colour `code-ground`
  `#f3f6f3` (note 4's code block), with its OKLCH value and ramp computed by the same
  helper the documenter used. Tidied the prose and sidecar sentences that had mentioned
  these sizes in passing. Re-ran the detector: only the 5.2px false positive remains.
  Frontmatter still parses (15 type roles, 17 colours); sidecar is valid JSON. Page
  unchanged.
