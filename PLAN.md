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

- Task: serve frontend pages with cleaner URLs without the html extension
- Signer: Magyari Ákos's agent
- Branch: feat/clean-frontend-urls
- Date: 2026-10-17

- Task: add dummy landing index and move employee page to employee path
- Signer: Magyari Ákos's agent
- Branch: feat/dummy-landing-index
- Date: 2026-10-17

- Task: Restyle the employee app to the Wise mobile design with shared Tailwind theme tokens.
- Signer: rcsenge's agent
- Branch: feat/wise-design-employee
- Date: 2026-10-17

- Task: Read invoice PDFs and photos with a local Ollama vision model. Send the extracted JSON through the existing invoice flow.
- Signer: Vilmos Babó's agent
- Branch: feat/ollama-invoice-reader
- Date: 2026-10-17

- Task: Expose the receipt country. Support more EU countries. Add many sample invoices for the demo.
- Signer: rcsenge's agent
- Branch: feat/sample-vat-countries
- Date: 2026-10-17

- Task: Restyle employer review to Wise design with per-country VAT. Make the employee app responsive.
- Signer: rcsenge's agent
- Branch: feat/wise-vat-by-country
- Date: 2026-10-17

- Task: Replace the generic VAT rule with sourced per-country rules. Support partial refundable shares in the backend.
- Signer: rcsenge's agent
- Branch: feat/backend-country-vat-rules
- Date: 2026-10-17
