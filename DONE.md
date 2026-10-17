# Done

This file records the completed work of every agent. An agent appends an entry after it finishes work. An agent never edits the entries of another agent.

## Signing

Sign every entry with the git user name. Add the suffix "'s agent" to the name. Use the value of `git config user.name`. List the commit hashes of the completed work.

## Entry Template

- Task: <description, under 25 words>
- Signer: <git config user.name>'s agent
- Branch: <current branch>
- Date: <YYYY-MM-DD>
- Commits: <commit hashes>

- Task: Connected the frontend to the backend. The employee page uploads the invoice JSON. Both pages read receipts and claims.
- Signer: Vilmos Babó's agent
- Branch: feat/connect-frontend-backend
- Date: 2026-10-17
- Commits: 56d98ec, 418088f, cffa53e, b8d194c, f786bc6, c25c534

---

- Task: serve frontend pages with cleaner URLs without the html extension
- Signer: Magyari Ákos's agent
- Branch: feat/clean-frontend-urls
- Date: 2026-10-17
- Commits: 2a306f6 f227d7b

---

- Task: add dummy landing index and move employee page to employee path
- Signer: Magyari Ákos's agent
- Branch: feat/dummy-landing-index
- Date: 2026-10-17
- Commits: 07b8f70 3608ef3

---

- Task: Restyle the employee app to the Wise mobile design with shared Tailwind theme tokens.
- Signer: rcsenge's agent
- Branch: feat/wise-design-employee
- Date: 2026-10-17
- Commits: c60e7d8, 735975a, f22e9a7

---

- Task: Read invoice PDFs and photos with a local Ollama vision model. Added sample PDFs and the frontend upload.
- Signer: Vilmos Babó's agent
- Branch: feat/ollama-invoice-reader
- Date: 2026-10-17
- Commits: 5b70afc, 831be7d, c0ed443, cf3055a, 6f37414

---

- Task: Expose the receipt country. Support more EU countries. Add many sample invoices for the demo.
- Signer: rcsenge's agent
- Branch: feat/sample-vat-countries
- Date: 2026-10-17
- Commits: 1ee2d6d, ac6da65, 0f34ff3

---

- Task: Restyle employer review to Wise design with per-country VAT. Make the employee app responsive.
- Signer: rcsenge's agent
- Branch: feat/wise-vat-by-country
- Date: 2026-10-17
- Commits: 712cf0c, c5b0e58

- Task: Containerized the backend and the Caddy frontend with Docker Compose. Ollama stays on the host.
- Signer: Magyari Ákos's agent
- Branch: feat/dockerize-backend
- Date: 2026-10-17
- Commits: 43339e7, 966c5e1, d4e03d3

---

- Task: Removed the dead generic rules engine. Updated the docs that referenced the old Decision type.
- Signer: Török Zaránd Tamás's agent
- Branch: refactor/remove-dead-rules-engine
- Date: 2026-10-17
- Commits: f0fb791, 0263a0b

---

- Task: Added SKILLS.md with the wise-design skill. AGENTS.md points to SKILLS.md for skill requests.
- Signer: rcsenge's agent
- Branch: docs/wise-design-skills
- Date: 2026-10-17
- Commits: a424c5b

---
