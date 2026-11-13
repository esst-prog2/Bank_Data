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
