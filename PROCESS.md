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
