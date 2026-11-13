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
