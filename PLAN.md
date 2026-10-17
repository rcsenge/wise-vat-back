# Plan

This file records the planned work of every agent. An agent appends an entry before it starts work. An agent never edits the entries of another agent.

## Signing

Sign every entry with the git user name. Add the suffix "'s agent" to the name. Use the value of `git config user.name`.

## Entry Template

- Task: <description, under 25 words>
- Signer: <git config user.name>'s agent
- Branch: <current branch>
- Date: <YYYY-MM-DD>

## Communication

Use `MESSAGES.md` for agent-to-agent messages. Read it frequently. Append new messages frequently. Pull frequently, so the file updates. Push frequently, so the other agents see the latest messages.

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

- Task: Add a golden corpus test suite with per-case expected files. Add an AI extraction evaluation script.
- Signer: Török Zaránd Tamás's agent
- Branch: feat/golden-corpus-testing
- Date: 2026-10-17

---

- Task: Remove the dead generic rules engine files from the domain module.
- Signer: Török Zaránd Tamás's agent
- Branch: refactor/remove-dead-rules-engine
- Date: 2026-10-17
- Date: 2026-10-17

---

- Task: Write a complete root README for the monorepo. Cover setup, Docker, local AI, demo data, API and team workflow.
- Signer: Vilmos Babó's agent
- Branch: docs/project-readme
- Date: 2026-10-17

---

- Task: Add SKILLS.md with the wise-design skill. Point to SKILLS.md from AGENTS.md.
- Signer: rcsenge's agent
- Branch: docs/wise-design-skills
- Date: 2026-10-17

---

- Task: Replace the generic VAT rule with sourced per-country rules. Support partial refundable shares in the backend.
- Signer: rcsenge's agent
- Branch: feat/backend-country-vat-rules
- Date: 2026-10-17

---

- Task: Match card transactions by country and date. Sum the claims over all approved invoices without the 500 record limit.
- Signer: rcsenge's agent
- Branch: fix/transaction-matching-claims
- Date: 2026-10-17

---

- Task: Write a root merge and push guide from our rebase mistakes. Reference it in AGENTS.md.
- Signer: Török Zaránd Tamás's agent
- Branch: docs/merge-guide
- Date: 2026-10-17

---

- Task: Accept only PDF and photo uploads. Reject JSON on the upload endpoint. Let the employee open the camera from the upload dialog.
- Signer: Vilmos Babó's agent
- Branch: feat/pdf-photo-camera-upload
- Date: 2026-10-17

---

- Task: Remove DONE.md. PLAN.md records every task. Update AGENTS.md, MERGE-GUIDE.md and README.md.
- Signer: rcsenge's agent
- Branch: chore/remove-done-file
- Date: 2026-10-17

---

- Task: Move the nested backend/backend folder up into backend. Update the Makefile, Docker, ignore rules and docs.
- Signer: Vilmos Babó's agent
- Branch: refactor/flatten-backend-folder
- Date: 2026-10-17

---

- Task: Add a rule that records new merge, pull and push problems in MERGE-GUIDE.md.
- Signer: Magyari Ákos's agent
- Branch: docs/record-merge-problems
- Date: 2026-10-17

---

- Task: Add a countdown page. The page counts down five minutes. The page shows the money that the world loses during the countdown.
- Signer: rcsenge's agent
- Branch: feat/money-loss-countdown
- Date: 2026-10-17

---

- Task: Make browsers revalidate frontend files on every load. A stale cached style.css broke the upload dialog on Windows.
- Signer: Vilmos Babó's agent
- Branch: fix/frontend-cache-revalidation
- Date: 2026-10-17

---

- Task: Add a mock database. It generates demo data for every supported country. Add a mock start mode.
- Signer: rcsenge's agent
- Branch: feat/mock-database
- Date: 2026-10-17

---

- Task: Rename the header name from vatback to SIGINT on the employee and employer pages. Change the avatar letter to S.
- Signer: Vilmos Babó's agent
- Branch: feat/sigint-header-name
- Date: 2026-10-17

---

- Task: Switch the default Ollama model to the faster non-thinking qwen2.5vl:7b.
- Signer: Magyari Ákos's agent
- Branch: feat/faster-vision-model
- Date: 2026-10-17

---

- Task: Remove the explaining text from the countdown page. Restyle the timer and the amount to the Wise visual language.
- Signer: rcsenge's agent
- Branch: feat/countdown-hide-explanation
- Date: 2026-10-17

---

- Task: Record the local AI latency findings and the fast extraction options in a root doc.
- Signer: Magyari Ákos's agent
- Branch: docs/ollama-latency-findings
- Date: 2026-10-17

---

- Task: Apply the 30 September refund deadline. Reject expired invoices on upload. Mark stored ones expired. Show deadlines in the frontend.
- Signer: Vilmos Babó's agent
- Branch: feat/claim-deadline
- Date: 2026-10-17

---

- Task: Add the hybrid accuracy comparison to OLLAMA-LATENCY.md.
- Signer: Magyari Ákos's agent
- Branch: docs/hybrid-accuracy
- Date: 2026-10-17

---
- Task: Change the countdown page to a desktop layout. Add a slowly rotating 3D globe beside the counter.
- Signer: rcsenge's agent
- Branch: feat/countdown-globe
- Date: 2026-10-17

---

- Task: Record the dead code and discrepancy findings in a root markdown file.
- Signer: Magyari Ákos's agent
- Branch: docs/repo-findings
- Date: 2026-10-17

---
- Task: Move the findings and latency notes into the need-to-implement folder.
- Signer: Magyari Ákos's agent
- Branch: chore/need-to-implement-folder
- Date: 2026-10-17

---
- Task: Add an append-only agent message file and its rules to AGENTS.md.
- Signer: Magyari Ákos's agent
- Branch: feat/agent-message-file
- Date: 2026-10-17

---
- Task: Add the frequent read, write, pull and push guidance to PLAN.md.
- Signer: Magyari Ákos's agent
- Branch: docs/plan-communication
- Date: 2026-10-17

---
- Task: Add the shared goal collaboration rule to AGENTS.md section 5.
- Signer: Magyari Ákos's agent
- Branch: docs/collaboration-guidance
- Date: 2026-10-17

---
- Task: Reword the collaboration rule for overlapping tasks from the user.
- Signer: Magyari Ákos's agent
- Branch: docs/collaboration-on-overlap
- Date: 2026-10-17

---
- Task: Add the team nickname to git user name map to section 5.
- Signer: Magyari Ákos's agent
- Branch: docs/team-name-aliases
- Date: 2026-10-17

---

- Task: Restyle the countdown globe after the Wise campaign page. Add a darker background and a faint SIGINT word.
- Signer: rcsenge's agent
- Branch: feat/countdown-globe-redesign
- Date: 2026-10-17

---
- Task: Unify the SIGINT branding in the frontend title tags and favicons. Cleanup item 5 of REPO-FINDINGS.md.
- Signer: rcsenge's agent
- Branch: fix/sigint-branding
- Date: 2026-10-17

---
