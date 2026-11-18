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

## New homework: ~30-second promo video for the page

- **Step 1 — install HyperFrames (2026-11-14)** — Prerequisites first: Node already
  v24.19.0 (satisfies 22+); FFmpeg wasn't installed, so installed it via
  `winget install --id Gyan.FFmpeg` (user's machine, system-wide). Its own `/plugin`
  route (`claude plugin marketplace add heygen-com/hyperframes`) isn't available in
  this VSCode-extension environment (same gap as Impeccable), so used the generic
  `npx skills add heygen-com/hyperframes` CLI path instead, run in the project root.
  Installed 9 skills (hyperframes, hyperframes-cli, hyperframes-registry, media-use,
  reverse-any-video, style-sampling, figma, remotion-to-hyperframes, slideshow) into
  `.agents/skills/`, symlinked into `.claude/skills/`, plus `skills-lock.json`. Only
  ~4.4 MB total, no bundled binaries this time, but still third-party tooling, not
  project content (same reasoning as Impeccable's install) — added all of it to
  `.gitignore` rather than committing. Note: HyperFrames isn't a "record this URL"
  tool — per its README, it's a framework for rendering an agent-authored HTML/CSS/
  GSAP composition to MP4; the actual video has to be composed from the promo page's
  real content (copy, screenshots, figures), not captured live. Still pending: like
  Impeccable, its skills won't be callable until this session restarts and reloads
  the skill list; FFmpeg also needs a shell restart to resolve on PATH (works today
  only via its absolute path). Decided: install now, finish composing the video in a
  fresh session once skills are live.
- **Step 2 — compose, render and embed the promo video (2026-11-15)** — HyperFrames started
  fine (CLI 0.9.52, FFmpeg now on PATH), so no screen-recording fallback. Its skills still
  weren't in the session's skill list (the session started outside the repo), so Claude read
  the `hyperframes`, `hyperframes-cli` and `media-use` skill files directly and followed them;
  skipped their optional telemetry "usage beacon" and feedback calls. Per the skill's launch-film
  workflow: wrote `promo-video/STORYLINES.md` (three storylines; since the user asked for the
  finished file, built the recommended one, "The number that comes twice", without a pick
  round) and `promo-video/SPEC.md` (DESIGN.md's tokens turned into numbers: Atlas Plate I
  paper/ink/greens, Archivo, amber only on disagreement). Film, 33.5 s: Erste's two RWA filings
  (149.7 vs 147.5bn, 1.5% apart) and Raiffeisen's (101.3 vs 100.9bn, 0.3%) land and turn
  amber → the pair shrinks into Austria's amber ring → the camera pulls back to the page's own
  28-bank map plate with its headline → the dashboard via the three real `docs/img/`
  screenshots (map/basket, concept picker, results table) → a 1.9x punch-in on the amber RWA
  row → "28 banks, every figure traced to its filing." on plate green → end card with the
  green "Open the interactive plate →" button and the site URL. Captions: one burned-in
  caption track (10 lines) carries the narration. Silent on purpose: it plays muted on the page,
  and music/voice would need a HeyGen sign-in (the user's step) or local tools nobody asked for.
  The map is the page's real SVG, lifted by `promo-video/tools/build_plate.py` (re-runnable),
  not redrawn. `hyperframes check` caught and Claude fixed: captions covering the Greek/Spanish
  markers (plate now settles at 0.86 scale), Raiffeisen's "0.3% apart" on screen too briefly,
  a 3 s dead stretch (now the 28 markers switch to the page's green "on" state), and a
  near-empty first frame/thumbnail (now opens on Erste's 149.7). Final check: 0 errors; kept
  warnings (silent film, small map numerals, intentional punch-in) are explained in
  `promo-video/REVIEW.md`. Rendered at delivery quality: H.264 1920x1080 30 fps, 4.7 MB,
  ffprobe 33.500 s; decoded frames from the MP4 match the snapshots. Embedded on
  `docs/index.html` as a new "The plate in 33 seconds" figure between the plate and the
  notes (`docs/video/bank-data-promo.mp4` + poster frame): click-to-play with controls, no
  autoplay (the brief limits motion to the one plate reveal), page's existing figure styles
  extended rather than new ones. A "Watch the 33-second tour" link in the cartouche was tried
  and reverted: at 1366x768 it wrapped the link row and clipped "Function snapshots and
  install" behind the legend. Browser-checked at 1920/1366/1280/390: no horizontal scroll, the
  main button still in the first screen, no script errors. `promo-video/` sources committed;
  its `.hyperframes/` history, `renders/` and the generated AGENTS.md/CLAUDE.md gitignored.
  Dashboard untouched.
- **Step 2, actually run (2026-11-16)** — Professor confirmed the Step 2 explanation above
  but asked for the real step: install gstack and run `/office-hours` on the finished promo
  page, since it doesn't yet say who Bank_Data is for. The npm package literally named
  `gstack` turned out to be an unrelated, unconnected package (confirmed by inspecting it
  before running anything); the real tool is Garry Tan's `github.com/garrytan/gstack`
  toolkit. Installed Bun (`winget install Oven-sh.Bun`, missing prerequisite), cloned the
  repo to `~/.claude/skills/gstack` (user-level, not project-local — the tool's own default,
  unlike Impeccable), and ran `./setup`, which registers Claude Code hooks in the user's
  global `~/.claude/settings.json`. Ran `/office-hours` in Builder/Learning mode on
  `docs/index.html`. Asked directly who the page is shown to; first honest answer was "the
  grader," which the tool pushed back on as conflating "who reads this submission" with
  "who the page's copy claims to serve" — a real distinction, not a dodge. Confirmed the
  honest on-page answer is PROMO_BRIEF.md's own stated primary users (analysts/researchers
  reconciling bank data across sources), not an invented pitch and not the grader. Ran the
  skill's premise-challenge and alternatives phases (design doc:
  `docs/designs/promo-page-audience-statement.md`); chose the smallest option — one sentence
  added to the existing hero lede — over a full lede rewrite or a new "for" label, to avoid
  re-touching copy Impeccable's critique pass had already scored. Decided: change the page
  only where the exercise actually convinced, nothing else; skipped the skill's full
  adversarial reviewer-dispatch loop and its startup/YC relationship-closing content as
  disproportionate to a one-sentence fix on a homework deadline.
- **Step 2, revision — the actual pick round (2026-11-16)** — Re-checked the whole video
  homework against its original instructions and found one real gap: the assignment's
  "suggest three really different ideas... then stop and wait for my choice" step never
  actually ran. The three storylines existed in `promo-video/STORYLINES.md` (A/B/C, each
  with what the viewer sees, the first three seconds, and what it adds to the page), but
  Step 2 above built A directly without presenting them and waiting, because the user had
  asked for the finished file. Fixed properly this time: presented all three storylines to
  the user via AskUserQuestion, with their full what-it-shows/first-3-seconds/what-it-adds
  descriptions, and waited. User chose **A — "The number that comes twice"** — the one
  already built and embedded. Decided: no re-render needed, since the shipped video is the
  one actually chosen under the real pick round; this entry is the record that the step
  ran for real, not a silent skip.
- **Step 2, compliance summary (2026-11-18)** — Walking the assignment's own instructions
  line by line against the steps above, so nothing here depends on reading between them:
  (1) *"Install HyperFrames... check that it renders"* — Step 1: installed, Node/FFmpeg
  confirmed, and it rendered the real film in Step 2 (CLI 0.9.52, no fallback needed).
  (2) *"Read my README, my promo page... use the page as a source of facts, not a script"*
  — Step 2: every figure, screenshot and the map plate came from `docs/index.html` and its
  data, not invented. (3) *"Suggest three really different ideas... two or three sentences
  [on] what the viewer sees, what the first three seconds show, what it adds to the page.
  Then stop and wait for my choice"* — `promo-video/STORYLINES.md` now carries all three
  fields for all three storylines (A/B/C); the actual stop-and-wait with the user ran in
  the "Step 2, revision" entry above, which is the authoritative record of this step, not
  Step 2's first pass (which built A without waiting — documented there as the gap this
  revision exists to close). (4) *"Make the video I choose... real screens and results...
  work without sound... check a few frames before you finish"* — Step 2: real dashboard
  screenshots and the page's own SVG map; silent by design; `hyperframes check` run, issues
  found and fixed, 0 errors at final check. (5) *"Put it on my promo page without changing
  anything else there"* — Step 2: embedded as a new figure between the plate and the notes;
  the one unrelated change tried (a cartouche link) was reverted for breaking layout at
  1366x768. (6) *"Add the step to my PROCESS.md"* / *"Push"* — this file, every step above;
  all commits pushed to `origin/main` (verified clean working tree, `main` matching
  `origin/main`, through this entry's own commit).
