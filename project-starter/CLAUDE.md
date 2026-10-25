@AGENTS.md

# Claude Code notes for this project

Shared rules are in AGENTS.md (imported above). The factory flow (contract, tickets, PRs, gates) is in `.claude/rules/factory.md`, which every session loads. Only Claude-specific notes go here.

- Where you run decides what runs. In a claude.ai project thread only this file, `.claude/CLAUDE.md` and `.claude/rules/*.md` load; hooks, `.claude/settings.json`, repo skills and `.mcp.json` do not. Skills come from the owner's account (Matt Pocock: `mattpocock-skills:*`). So never rely on a local hook: the gates are the GitHub checks.
- Locally (Claude Code CLI or desktop) the global `~/.claude/CLAUDE.md`, hooks and `.claude/verify.json` add a verify gate at Stop; the GitHub checks still decide the merge.
- Skills to prefer here: <e.g. `shadcn`, `vercel-react-best-practices`; or `officecli` / `xlsx` for reports>.
- Browser check: dev server on <http://localhost:3000>; use the built-in browser pane or the Playwright MCP.
- UI work follows `DESIGN.md`; if it is still the empty stub, run `impeccable` to agree a direction with the owner first.
- Rules for specific paths are in `.claude/rules/*.md` with `paths:` (loaded locally, when matching files are touched). A rule every session must see goes in a file without `paths:`.
