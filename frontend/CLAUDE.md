# Claude Code Operating Notes

These notes govern how Claude works in the frontend project. They complement the shared directives. Read @AGENTS.md first, then apply these notes.

## Role
- You operate the frontend project of the SIGINT monorepo.
- The backend lives in `../backend`. Edit it only when the user asks.

## Work Habits
- Read the relevant file before changing it. Never guess its contents.
- Follow the design system and Tailwind rules in @AGENTS.md.
- Keep every change small and sequential. Make one logical change per commit.

## Verification
- State exactly what you changed and what you verified.
- If a command fails, read the error and report the cause.

## Output Style
- Follow the coding standards in @AGENTS.md. Follow the ASD-STE100 rules.
- Give short and simple answers. Write simple English.
- Include only what matters. Do not add long text.
- Show a file path in every message that touches a file.
