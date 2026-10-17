# Merge and Push Guide

This guide records the merge, pull, and push problems we found. Read it before you rebase, merge, or push. The notes prevent wasted time.

## 1. The editor block

`git rebase --continue` opens an editor and waits for input. The process stalls silently for minutes.

Run the rebase without the editor.

```
GIT_EDITOR=true git rebase --continue
```

Use `GIT_EDITOR=true` for amends and similar commands that open an editor.

```
GIT_EDITOR=true git commit --amend --no-edit
```

## 2. Coordination conflict resolution

PLAN.md conflicts often. Every agent appends to it.

Keep both entries. Keep them in order. Place a `---` line after every entry.

Never delete another agent's entry.

## 3. The leftover marker

The `<<<<<<< HEAD` line sits above the conflict block. Removing the block can leave that line behind. We committed a marker several times.

Scan for markers before you stage and before you continue the rebase.

```
grep -rnE '<<<<<<<|=======|>>>>>>>' PLAN.md
```

Scan again after the rebase finishes. A marker in main needs a fix commit.

## 4. The rejected push

Teammates push frequently. The push fails with a non-fast-forward error.

Never force push. The hooks block it for a reason.

Fetch. Read the new commits. Rebase onto origin/main.

Repeat if the remote moves again. The conflicts stay small.

## 5. Origin moved while you worked

Local main goes stale during a long merge.

Save your work on a branch. Reset local main to origin/main. Then merge.

```
git branch save/<name> <your-commit>
git checkout main
git reset --hard origin/main
git merge --ff-only save/<name>
```

## 6. Deleted the branch too early

A rejected push is not a reason to delete work.

Recreate the branch from your local commit. The work survives in local main.

```
git branch feat/<name> <local-main-commit>
```

## 7. The silent file whitelist

The .gitignore is a whitelist. It ignores every path by default. A new directory vanishes from staging without a warning.

After you add files, run `git status`. Confirm every new file appears.

Add a `!` line to .gitignore for a new allowed path.

## 8. Line ending churn

An editor on Windows can rewrite a file with CRLF. The repository stores LF. Git then shows the whole file as changed. The diff hides your real edit.

Normalize the file before you commit. Remove the carriage return bytes.

```
python -c "open('PLAN.md','wb').write(open('PLAN.md','rb').read().replace(b'\r\n', b'\n'))"
```

The root .gitattributes forces LF for markdown files. Keep every markdown file in LF.

## 9. The golden data gotcha

A teammate rule change can make generated fixtures stale. The golden corpus fails.

Regenerate the artifact. Do not weaken a test to make it pass.

```
make golden
```

## 10. Add a new problem note

A new merge, pull, or push problem appears. The guide does not describe it. Add the note so the next agent does not lose time.

Use the next free section number. State the problem and its fix. Use the shape of the other sections.

Put the commands in a code block. Add a checklist step when the fix changes an existing step.

## 11. The inactive hooks

A fresh clone does not read `.githooks/`. A commit on main then succeeds without a warning.

Check the hook path at session start. Set it when the value is empty.

```
git config core.hooksPath
git config core.hooksPath .githooks
```

A commit landed on local main. Move it to a branch before you push.

```
git checkout -b feat/<name> origin/main
git cherry-pick <commit>
git branch -f main origin/main
```

## 12. The shared worktree branch race

Another agent runs git in the same working directory. Two agent processes share the checkout. One can switch the branch while the other rebases.

The branch name and the index change under you. Your rebase lands on the other branch. The reflog shows the branch switch.

Use a dedicated worktree for the rebase.

```
git worktree add /tmp/<worktree-name> <branch>
git -C /tmp/<worktree-name> rebase origin/main
```

Run every git write in the worktree. Check the branch before you push.

```
git branch --show-current
```

Delete the worktree after the merge.

## Finish checklist

1. Fetch. Read the new commits.
2. Rebase onto origin/main. Use GIT_EDITOR=true.
3. Resolve conflicts. Keep both entries in order.
4. Scan every marker. Fix the leftovers.
5. Normalize markdown to LF.
6. Run the full test suite.
7. Merge with --ff-only. Push. Delete the branch.

