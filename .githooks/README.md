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
- `pre-push` blocks force pushes to `main`. It also blocks pushes of a
  feature branch to `main`.

## Workflow

Work on a short-lived feature branch. Merge the branch to `main` and push:

```
git checkout -b feat/my-change
# edit and commit on the branch
git checkout main
git merge --ff-only feat/my-change
git push origin main
git branch -d feat/my-change
```

## Server-Side Enforcement

These hooks run on the local machine. A bypass is possible with
`git commit --no-verify`. For true server-side enforcement, enable GitHub
rulesets or branch protection on `main`. The free tier does not support
them for private repositories.
