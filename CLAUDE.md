# Claude Code Operating Notes

These notes govern how Claude works in this monorepo. They complement the shared directives. Read @AGENTS.md first, then apply these notes.

## Monorepo
- This repository is a monorepo with multiple project folders.
- Each project folder has its own @AGENTS.md and @CLAUDE.md file.
- Current projects: `backend/` and `frontend/`. New projects may appear later.

## Coordination
- You run as a standalone agent. You finish one deep task alone.
- Pi agents form a swarm. They share state through `PLAN.md`.
- Read `AGENTS.md` section 5.6 for the cooperation rules.
- Append a signed entry in `PLAN.md` when you claim or finish work.

## Scope
- Work in ONE project per task. Work in more only when the user asks.
- Use only the root @AGENTS.md and the project @AGENTS.md.
- Read the project @CLAUDE.md when the folder has one.

## Work Habits
- Read a file before you change it. Never guess its contents.
- Keep every change small and sequential. Make one logical change per commit.

## Output Style
- Follow the coding standards in @AGENTS.md. Follow the ASD-STE100 rules.
- Give short and simple answers. Write simple English.
- Include only what matters. Do not add long text.
- Show a file path in every message that touches a file.
