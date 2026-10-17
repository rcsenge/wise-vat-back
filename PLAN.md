# Plan

This file records the planned work of every agent. An agent appends an entry before it starts work. An agent never edits the entries of another agent.

## Signing

Sign every entry with the git user name. Add the suffix "'s agent" to the name. Use the value of `git config user.name`.

## Entry Template

- Task: <description, under 25 words>
- Signer: <git config user.name>'s agent
- Branch: <current branch>
- Date: <YYYY-MM-DD>

- Task: Connect the frontend to the backend. Upload the invoice JSON. Show stored receipts and claims from the backend.
- Signer: Vilmos Babó's agent
- Branch: feat/connect-frontend-backend
- Date: 2026-10-17

---

- Task: serve frontend pages with cleaner URLs without the html extension
- Signer: Magyari Ákos's agent
- Branch: feat/clean-frontend-urls
- Date: 2026-10-17

---

- Task: add dummy landing index and move employee page to employee path
- Signer: Magyari Ákos's agent
- Branch: feat/dummy-landing-index
- Date: 2026-10-17

---

- Task: Restyle the employee app to the Wise mobile design with shared Tailwind theme tokens.
- Signer: rcsenge's agent
- Branch: feat/wise-design-employee
- Date: 2026-10-17

---

- Task: Read invoice PDFs and photos with a local Ollama vision model. Send the extracted JSON through the existing invoice flow.
- Signer: Vilmos Babó's agent
- Branch: feat/ollama-invoice-reader
- Date: 2026-10-17

---

- Task: Expose the receipt country. Support more EU countries. Add many sample invoices for the demo.
- Signer: rcsenge's agent
- Branch: feat/sample-vat-countries
- Date: 2026-10-17

---

- Task: Restyle employer review to Wise design with per-country VAT. Make the employee app responsive.
- Signer: rcsenge's agent
- Branch: feat/wise-vat-by-country
- Date: 2026-10-17

---

- Task: Create a mockdata project. Render the backend mock invoices in Typst and compile them into PDFs.
- Signer: Magyari Ákos's agent
- Branch: feat/mock-invoices-typst
- Date: 2026-10-17

---

- Task: Containerize the backend and the Caddy frontend with Docker Compose. Keep Ollama on the host.
- Signer: Magyari Ákos's agent
- Branch: feat/dockerize-backend
- Date: 2026-10-17

---

- Task: Add the init launcher. It starts Ollama and runs Docker Compose.
- Signer: Magyari Ákos's agent
- Branch: feat/init-script
- Date: 2026-10-17

---

- Task: Remove the dead generic rules engine files from the domain module.
- Signer: Török Zaránd Tamás's agent
- Branch: refactor/remove-dead-rules-engine
- Date: 2026-10-17
- Date: 2026-10-17

---

- Task: Add SKILLS.md with the wise-design skill. Point to SKILLS.md from AGENTS.md.
- Signer: rcsenge's agent
- Branch: docs/wise-design-skills
- Date: 2026-10-17

---
