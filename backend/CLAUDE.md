# Claude Code Operating Notes

These notes govern how Claude works in this repository. They complement the shared directives. Read @AGENTS.md first, then apply these notes.

## Role
- You operate the FastAPI backend for Wise VAT Back.
- The frontend lives in `../frontend`. Do not edit it here.

## Work Habits
- Read the relevant file before changing it. Never guess its contents.
- Prefer the Makefile targets over raw commands. Use uv for every Python step.
- Run `make test` after any code change. Keep the suite green.
- Keep every change small and sequential. Make one logical change per commit.

## Build Strategy
- Mock every component you can. Hardcode data where possible.
- Build in demo order first. Wire the real service later.
- The goal is a demoable backend that connects to the frontend.

## Verification
- State exactly what you changed and what you verified.
- Never claim success without a passing test run.
- If a command fails, read the error and report the cause.

## Output Style
- Follow the coding standards in AGENTS.md. Follow the ASD-STE100 rules.
- Give short and simple answers. Write simple English.
- Include only what matters. Do not add long text.
- Show a file path in every message that touches a file.

## Monorepo Note
This project is part of the SIGINT monorepo. Shared rules live in the root `@../AGENTS.md`.
Edit the frontend only when the user asks. Read the root and the frontend `@../frontend/AGENTS.md` before you touch frontend files.
