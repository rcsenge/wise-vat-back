# Git Hooks

These hooks enforce the repository workflow. Git reads hooks from this
directory because `core.hooksPath` points here.

## Setup

Each developer runs these commands once after cloning and once after
authenticating:

```
git config core.hooksPath .githooks
gh auth login
```

## Hooks

- `pre-commit` blocks commits on `main`. It also runs Prettier with the
  Tailwind plugin on staged HTML and CSS files.
- `pre-merge-commit` blocks local merges that commit onto `main`.
- `pre-push` blocks every push to `main`. It also blocks force pushes and
  pushes of a feature branch to `main`.

## Mandatory Pull Request Workflow

Code reaches `main` only through a pull request. Use the GitHub CLI:

```
git push -u origin <branch>
gh pr create --fill
gh pr review --approve
gh pr merge --merge
git checkout main
git pull
```

## Server-Side Enforcement

These hooks run on the local machine. A bypass is possible with
`git commit --no-verify`. For true server-side enforcement, enable GitHub
rulesets or branch protection on `main`. The free tier does not support
them for private repositories.
