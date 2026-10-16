# Git Hooks

These hooks enforce the repository workflow. Git reads hooks from this
directory because `core.hooksPath` points here.

## Setup

Each developer runs this command once after cloning:

```
git config core.hooksPath .githooks
```

## Hooks

- `pre-commit` blocks commits on `main`. It also runs Prettier with the
  Tailwind plugin on staged HTML and CSS files.
- `pre-push` blocks pushes of a non-main branch to `main`. It also blocks
  force pushes to `main`.

## Server-Side Enforcement

These hooks run on the local machine. For full enforcement, enable GitHub
branch protection on `main`. Require a pull request before merge.
