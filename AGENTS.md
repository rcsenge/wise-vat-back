# AI Agent System Directives

You are an AI coding agent operating in a frontend repository. Read and apply these directives before executing any workflow. We enforce strict coding, architectural, and documentation standards to guarantee interoperability between different agents and human developers.

## 1. Project Configuration
- **Language:** HTML
- **Framework:** Tailwind CSS
- **Design System:** Tailwind v4
- **Mobile App:** Capacitor by Ionic
- **Python Tooling:** UV
- **Web Server:** Caddy
- **Documentation Language:** English
- **Commit Message Language:** English

## 2. Git & Version Control Workflow
Apply Trunk-Based Development with strict commit hygiene. Use this workflow for every change, including documentation edits. Git hooks in `.githooks/` enforce the workflow. Never bypass the hooks. A bypass is a critical defect.

### 2.1. Branching
- **Branch Before Edit:** Create a feature branch off `main` before any edit. Never commit directly on `main`.
- **Hard Prohibition:** Never run `git commit` on `main`. Never bypass the hooks. The actions are forbidden in all cases.
- **Short-Lived Branches:** Keep the branch lifespan under one day. Merge the branch back when complete.
- **No Branch Push:** Never push a feature branch to `main`. Push `main` only after a merge.

### 2.2. Committing
- **Atomic Commits:** A commit must do exactly one thing (one feature, one fix, or one refactor).
- **Smaller Frequent Commits:** Prefer small, frequent commits over large sprawling ones. Split work into the smallest logically complete units.
- **Rebase WIPs:** You may write small Work-In-Progress (WIP) commits locally. Before merging, rebase and squash these WIP commits into larger, logically complete atomic commits.
- **Working State Guarantee:** Every commit must load and render without errors. Do not leave broken states in the commit log.
- **Conventional Commits:** Prefix all commit messages with standard tags (`feat:`, `fix:`, `refactor:`, `chore:`). Write all commit messages in English.

### 2.3. Merging and Pushing
- **Merge to Main:** Check out `main`. Merge the feature branch after the final commit.
- **Push Main:** Push the merged `main` to the remote origin.
- **Delete Branch:** Delete the feature branch after the merge.

### 2.4. File Tracking
- **Whitelist Only:** The `.gitignore` is a whitelist. It ignores every path by default. It re-includes only allowed paths.
- **New File Check:** Confirm an untracked file is allowed before you add it. Do not force-add ignored paths.

### 2.5. No Workarounds
- **No Hook Bypass:** Never use `--no-verify`. The flag defeats the enforcement.
- **No Force Push:** Never use `--force`. The flag defeats the enforcement.
- **Critical Defect:** A bypass is a critical defect. Stop the workflow. Create a branch and restart.

## 3. Frontend Coding Standards
We optimize for safety, predictability, and simplicity. Apply these rules to all markup and styling.

### 3.1. Execution and Safety
- **Explicit Limits:** Bound all loops, animations, and resource loads to prevent latency spikes.
- **Fail Early:** Validate all form inputs and data at the boundary. Reject bad data immediately.

### 3.2. Complexity
- **Simplify Structure:** Keep markup and class composition minimal. Minimize branches at the point of use. Control flow must be strictly sequential where possible.
- **Zero Technical Debt:** Write the optimal, final version on the first attempt. Do not leave `TODO: fix later` comments.

### 3.3. Naming and Structure
- **Casing:** Use `kebab-case` for class and id names.
- **Big-Endian Naming:** Sort names by the most significant word first (e.g., `card-header-title` instead of `title-card-header`).
- **No Abbreviations:** Do not abbreviate names. Use the exact number of characters needed for absolute clarity.

### 3.4. Tailwind CSS
- **Utility Classes:** Build all styling with Tailwind utility classes directly in the markup.
- **No Custom CSS:** Use the Tailwind theme for colors, spacing, and typography. Write custom CSS only when Tailwind cannot express the design.
- **No Inline Styles:** Do not use inline `style` attributes.
- **Responsive First:** Use mobile-first breakpoints with Tailwind prefixes (`sm:`, `md:`, `lg:`, `xl:`).
- **Semantic Markup:** Use semantic HTML elements. Keep the interface accessible with labels, alt text, and proper heading order.

## 4. Documentation & Output (ASD-STE100)
All code comments, commit messages, and agent-to-agent communications must follow Simplified Technical English (ASD-STE100) rules to prevent machine misparsing.

- **Length Caps:** Write maximum 20 words for instructions. Write maximum 25 words for descriptions.
- **One Instruction Per Sentence:** Do not use "and" or "then" to join steps.
- **Active Voice:** The subject must perform the action (e.g., "The script renders the page.").
- **No Semicolons:** Semicolons permit run-on sentences. Use a period. Start a new sentence.
- **No Phrasal Verbs:** Avoid two-word verbs ("spin up", "take down"). Use precise verbs ("start", "stop").
- **One Word, One Meaning:** Pick one term for a concept and use it every time. Do not rotate synonyms to sound creative.
