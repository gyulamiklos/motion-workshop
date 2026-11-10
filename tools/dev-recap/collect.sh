#!/usr/bin/env bash
# What changed in some repos over a period, read-only: non-merge commits on all local branches and,
# when the repo has a GitHub remote and gh is signed in, the pull requests merged in the period.
# Usage: tools/dev-recap/collect.sh --since YYYY-MM-DD [--until YYYY-MM-DD] <repo dir>... > changes.json
# Nothing is fetched or checked out: it reads what is already in the local clones (run git fetch yourself
# first if the clone is stale).
set -eu
SINCE="" UNTIL=""
repos=()
while [ $# -gt 0 ]; do
  case "$1" in
    --since) SINCE=$2; shift 2 ;;
    --until) UNTIL=$2; shift 2 ;;
    *) repos+=("$1"); shift ;;
  esac
done
[ -n "$SINCE" ] && [ ${#repos[@]} -gt 0 ] || { echo "usage: collect.sh --since YYYY-MM-DD [--until YYYY-MM-DD] <repo>..." >&2; exit 2; }
UNTIL=${UNTIL:-$(date +%F)}

python3 -I - "$SINCE" "$UNTIL" "${repos[@]}" <<'PY'
import json, os, re, subprocess, sys

since, until, repos = sys.argv[1], sys.argv[2], sys.argv[3:]

def run(args, cwd):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True).stdout

out = {"since": since, "until": until, "repos": []}
for repo in repos:
    repo = os.path.abspath(repo)
    name = os.path.basename(repo)
    fmt = "%x1e%H%x1f%h%x1f%aI%x1f%an%x1f%s%x1f%D"
    raw = run(["git", "log", "--all", "--no-merges", f"--since={since} 00:00", f"--until={until} 23:59:59", f"--format={fmt}", "--shortstat"], repo)
    commits = []
    for block in raw.split("\x1e"):
        block = block.strip("\n")
        if not block.strip():
            continue
        head, _, stat = block.partition("\n")
        parts = head.split("\x1f")
        if len(parts) < 6:
            continue
        full, short, date, author, subject, refs = parts[:6]
        m = re.findall(r"(\d+) (file|insertion|deletion)", stat)
        nums = {k: int(v) for v, k in m}
        commits.append({"hash": short, "date": date[:10], "author": author, "subject": subject,
                        "files": nums.get("file", 0), "insertions": nums.get("insertion", 0), "deletions": nums.get("deletion", 0)})
    remote = run(["git", "remote", "get-url", "origin"], repo).strip()
    prs, pr_note = [], None
    gh_repo = re.search(r"github\.com[:/](.+?)(?:\.git)?$", remote)
    if gh_repo:
        res = subprocess.run(["gh", "pr", "list", "-R", gh_repo.group(1), "--state", "merged", "--limit", "200",
                              "--search", f"merged:{since}..{until}",
                              "--json", "number,title,author,mergedAt,additions,deletions,changedFiles,headRefName,body"],
                             capture_output=True, text=True)
        if res.returncode == 0:
            for p in json.loads(res.stdout or "[]"):
                prs.append({"number": p["number"], "title": p["title"], "author": (p.get("author") or {}).get("login"),
                            "merged": (p.get("mergedAt") or "")[:10], "branch": p.get("headRefName"),
                            "additions": p.get("additions"), "deletions": p.get("deletions"), "files": p.get("changedFiles"),
                            "body": (p.get("body") or "")[:600]})
        else:
            pr_note = "gh failed: " + res.stderr.strip()[:200]
    else:
        pr_note = "no GitHub remote"
    out["repos"].append({"name": name, "path": repo, "commits": commits, "merged_prs": prs, "pr_note": pr_note,
                         "authors": sorted({c["author"] for c in commits})})
json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
print()
PY
