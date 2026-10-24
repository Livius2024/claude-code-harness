@AGENTS.md

# Claude Code notes for this project

Shared rules are in AGENTS.md (imported above). Only Claude-specific notes go here; skills, hooks and the answer format come from the global `~/.claude/CLAUDE.md`.

- Skills to prefer here: <e.g. `shadcn`, `vercel-react-best-practices`, `better-auth-best-practices`; or `officecli` / `xlsx` for reports>.
- Browser check: dev server on <http://localhost:3000>; use the built-in browser pane or the Playwright MCP.
- UI work follows `DESIGN.md`; if it is still the empty stub, run `impeccable` to agree a direction with the owner first.
- Rules for specific paths are in `.claude/rules/*.md` (loaded only when matching files are touched). Add new ones there instead of growing this file.
