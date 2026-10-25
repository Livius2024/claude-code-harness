@AGENTS.md

# Claude Code notes for this repository

This repo holds the owner's Claude Code + Codex factory setup: the `project-starter/` template copied into every new project, and the Romanian guide in `README.md`. It is not an application.

- Cloud threads load only this file, `.claude/CLAUDE.md` and `.claude/rules/*.md` without `paths:`. Hooks and `.claude/settings.json` do not run there, so a change that relies on them must say it works only locally.
- The owner reads Romanian: `README.md` and `project-starter/docs/github-gates.md` stay in Romanian; agent-facing files (AGENTS.md, CLAUDE.md, rules, scripts) in English.
