# AI Agent System Directives

You are an AI coding agent operating in a frontend repository. Read and apply these directives before executing any workflow. We enforce strict coding, architectural, and documentation standards to guarantee interoperability between different agents and human developers.

## 1. Project Configuration
- **Language:** HTML
- **Framework:** Tailwind CSS
- **Design System:** Tailwind v4
- **Mobile App:** Capacitor by Ionic
- **Web Server:** Caddy
- **Documentation Language:** English
- **Commit Message Language:** English

## 2. Git & Version Control Workflow
Apply Trunk-Based Development with feature branching and strict commit hygiene.
- **Short-Lived Branches:** Branch off `main` for each feature. Keep the branch lifespan under one day and merge back. Do not push directly to `main`.
- **Atomic Commits:** A commit must do exactly one thing (one feature, one fix, or one refactor).
- **Smaller Frequent Commits:** Prefer small, frequent commits over large sprawling ones. Split work into the smallest logically complete units.
- **Rebase WIPs:** You may write small Work-In-Progress (WIP) commits locally. Before merging, rebase and squash these WIP commits into larger, logically complete atomic commits.
- **Working State Guarantee:** Every commit must load and render without errors. Do not leave broken states in the commit log.
- **Conventional Commits:** Prefix all commit messages with standard tags (`feat:`, `fix:`, `refactor:`, `chore:`). Write all commit messages in English.

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
