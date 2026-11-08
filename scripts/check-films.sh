#!/usr/bin/env bash
# Runs `hyperframes check` on the films changed since their last passing check, or on all with --all.
# Films are not in git (projects/ is ignored), so "changed" means a file newer than the film's .last-check.
# Usage: scripts/check-films.sh [--all]      Exit code: 0 if every checked film passes.
set -u
cd "$(dirname "$0")/.." || exit 1
V=$(tr -d '[:space:]' < hyperframes.version)
if [ "${1:-}" = "--all" ]; then
  films=$(ls -d projects/*/ 2>/dev/null | sed 's|/$||')
else
  films=""
  for f in projects/*/; do
    f=${f%/}
    [ -f "$f/.last-check" ] && [ -z "$(find "$f" -type f -newer "$f/.last-check" -not -path '*/node_modules/*' -not -path '*/out/*' -not -path '*/.hyperframes/*' | head -1)" ] && continue
    films="$films $f"
  done
fi
fail=0; n=0
for f in $films; do
  [ -f "$f/index.html" ] || continue
  n=$((n + 1))
  if out=$(cd "$f" && DO_NOT_TRACK=1 npx -y "hyperframes@$V" check 2>&1); then echo "ok    $f"; touch "$f/.last-check"
  else echo "$out" | grep -iE "error|✗" | head -15; echo "FAIL  $f"; fail=1; fi
done
[ $n -eq 0 ] && echo "no changed film to check"
exit $fail
