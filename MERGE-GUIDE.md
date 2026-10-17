# Merge and Push Guide

This guide records the merge and push problems we found. Read it before you rebase, merge, or push. The notes prevent wasted time.

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

## Finish checklist

1. Fetch. Read the new commits.
2. Rebase onto origin/main. Use GIT_EDITOR=true.
3. Resolve conflicts. Keep both entries in order.
4. Scan every marker. Fix the leftovers.
5. Normalize markdown to LF.
6. Run the full test suite.
7. Merge with --ff-only. Push. Delete the branch.
