# AI Agent System Directives

You are an AI coding agent operating in the SIGINT monorepo. Read and apply these directives before executing any workflow. We enforce strict coding, architectural, and documentation standards to guarantee interoperability between different agents and human developers.

## 0. Monorepo Structure

This repository is a monorepo. It contains multiple project folders. The root `AGENTS.md` holds the project-wide rules for every project. Each project folder holds its own project-specific rules.

Current projects: `backend/` and `frontend/`. New projects may appear later.

Read the project `AGENTS.md` before you edit any file inside that folder. Read the project `CLAUDE.md` when the folder has one.

Work in ONE project only. Work in more than one project only when the user asks for it explicitly.

Use ONLY the root `AGENTS.md` and the `AGENTS.md` of the current project. Do not read any other project `AGENTS.md`.

## 1. Project Configuration
- **Serving:** Prefer Caddy as the web server for the app.

## 2. Package Management
- **Mandate:** Install all dependencies only with pnpm. Never use npm or yarn.
- **Lockfile:** Track `pnpm-lock.yaml`. Reject `package-lock.json` and `yarn.lock`.
- **Syntax:** Use `pnpm install`, `pnpm add`, and `pnpm run <script-name>`.
- **Scripts:** Reference local binaries directly. Do not prefix with `npx`.
- **Build Scripts:** Approve builds in `pnpm-workspace.yaml`. Do not use `--unsafe-perm`.

## 3. Git & Version Control Workflow
Apply Trunk-Based Development with strict commit hygiene. Use this workflow for every change, including documentation edits. Git hooks in `.githooks/` enforce the workflow. Never bypass the hooks. A bypass is a critical defect.

### 3.1. Session Start
- **Pull First:** Pull the latest `main` at the start of every work session.
- **Read Changes:** Read every pulled commit. Understand each change before work.
- **Apply Changes:** Incorporate the new behavior into the design and the work.

### 3.2. Branching
- **Branch Before Edit:** Create a feature branch off `main` before any edit. Never commit directly on `main`.
- **Hard Prohibition:** Never run `git commit` on `main`. Never bypass the hooks. The actions are forbidden in all cases.
- **Short-Lived Branches:** Keep the branch lifespan under one day. Merge the branch back when complete.
- **No Branch Push:** Never push a feature branch to `main`. Push `main` only after a merge.

### 3.3. Committing
- **Atomic Commits:** A commit must do exactly one thing (one feature, one fix, or one refactor).
- **Smaller Frequent Commits:** Prefer small, frequent commits over large sprawling ones. Split work into the smallest logically complete units.
- **Rebase WIPs:** You may write small Work-In-Progress (WIP) commits locally. Before merging, rebase and squash these WIP commits into larger, logically complete atomic commits.
- **Working State Guarantee:** Every commit must load and render without errors. Do not leave broken states in the commit log.
- **Conventional Commits:** Prefix all commit messages with standard tags (`feat:`, `fix:`, `refactor:`, `chore:`). Write all commit messages in English.

### 3.4. Merging and Pushing
- **Merge to Main:** Check out `main`. Merge the feature branch after the final commit.
- **Push Main:** Push the merged `main` to the remote origin.
- **Delete Branch:** Delete the feature branch after the merge.

### 3.5. File Tracking
- **Whitelist Only:** The `.gitignore` is a whitelist. It ignores every path by default. It re-includes only allowed paths.
- **New File Check:** Confirm an untracked file is allowed before you add it. Do not force-add ignored paths.

### 3.6. No Workarounds
- **No Hook Bypass:** Never use `--no-verify`. The flag defeats the enforcement.
- **No Force Push:** Never use `--force`. The flag defeats the enforcement.
- **Critical Defect:** A bypass is a critical defect. Stop the workflow. Create a branch and restart.

## 4. Documentation & Output (ASD-STE100)
All code comments, commit messages, and agent-to-agent communications must follow Simplified Technical English (ASD-STE100) rules to prevent machine misparsing.

- **Length Caps:** Write maximum 20 words for instructions. Write maximum 25 words for descriptions.
- **One Instruction Per Sentence:** Do not use "and" or "then" to join steps.
- **Active Voice:** The subject must perform the action (e.g., "The script renders the page.").
- **No Semicolons:** Semicolons permit run-on sentences. Use a period. Start a new sentence.
- **No Phrasal Verbs:** Avoid two-word verbs ("spin up", "take down"). Use precise verbs ("start", "stop").
- **One Word, One Meaning:** Pick one term for a concept and use it every time. Do not rotate synonyms to sound creative.
