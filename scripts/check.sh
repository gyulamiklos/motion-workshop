#!/usr/bin/env bash
# One command for "is it green": workshop doctor, then `hyperframes check` on the changed films. Short output, "OK" on success.
# Usage: scripts/check.sh [--staged] [base]
#   --staged  check only (no rewrite), on the staged files; the pre-commit hook uses this
#   base      what counts as changed (default: HEAD)
# Exit code: 0 if everything passed, 1 otherwise.
# Works with the bash 3.2 that ships with macOS and with Linux bash.
# Limitation: --staged checks the working-tree version of the staged files, so a partially
# staged file is checked as it is on disk.
set -u
cd "$(git rev-parse --show-toplevel)" || exit 1

# --- configuration (set by project-setup; an empty value skips the step; the environment can override) ---
EXTS=${EXTS-""}                         # file extensions to format, space separated
FORMAT_CHECK=${FORMAT_CHECK-""} # gets the files as arguments, fails if unformatted
FORMAT_FIX=${FORMAT_FIX-""}       # gets the files as arguments, formats them
LINT=${LINT-"scripts/doctor.sh"}
TEST=${TEST-"scripts/check-films.sh"}
TEST_ARGS_NOT_MACOS=${TEST_ARGS_NOT_MACOS-""}   # extra test arguments off macOS, e.g. --exclude-tags golden
# ---

case "$EXTS$FORMAT_CHECK$FORMAT_FIX$LINT$TEST" in
  *'{{'*) echo "ERROR: scripts/check.sh is not configured (a {{placeholder}} is left in its configuration block)"; echo "FAILED"; exit 1 ;;
esac

STAGED=0; [ "${1:-}" = "--staged" ] && { STAGED=1; shift; }
BASE=${1:-HEAD}
fail=0

# A missing base must not look like "nothing changed".
if ! git rev-parse --verify --quiet "$BASE^{commit}" >/dev/null 2>&1; then
  if [ "$BASE" != "HEAD" ]; then echo "ERROR: base does not exist: $BASE"; echo "FAILED"; exit 1; fi
fi

# Runs a configured command; appends the files unless the command already uses "$@".
run_with_files() {
  local cmd=$1; shift
  case "$cmd" in
    *'"$@"'*) bash -c "$cmd" _ "$@" ;;
    *) bash -c "$cmd \"\$@\"" _ "$@" ;;
  esac
}

specs=()
for e in $EXTS; do specs+=("*.$e"); done

files=()
if [ ${#specs[@]} -gt 0 ]; then
  if [ $STAGED -eq 1 ]; then
    while IFS= read -r f; do [ -n "$f" ] && files+=("$f"); done \
      < <(git diff --cached --name-only --diff-filter=ACMR -- "${specs[@]}")
  else
    while IFS= read -r f; do [ -n "$f" ] && [ -f "$f" ] && files+=("$f"); done \
      < <({ git diff --name-only "$BASE" -- "${specs[@]}" 2>/dev/null; git ls-files --others --exclude-standard -- "${specs[@]}"; } | sort -u)
  fi
fi

if [ ${#files[@]} -eq 0 ]; then
  echo "== Format: no changed files"
elif [ $STAGED -eq 1 ] && [ -n "$FORMAT_CHECK" ]; then
  echo "== Format check (${#files[@]} files)"
  out=$(run_with_files "$FORMAT_CHECK" "${files[@]}" 2>&1) \
    || { echo "$out" | tail -15; echo "ERROR: unformatted files; run scripts/check.sh without --staged to fix"; fail=1; }
elif [ $STAGED -eq 0 ] && [ -n "$FORMAT_FIX" ]; then
  echo "== Format (${#files[@]} files)"
  out=$(run_with_files "$FORMAT_FIX" "${files[@]}" 2>&1) || { echo "$out" | tail -15; fail=1; }
fi

if [ -n "$LINT" ]; then
  echo "== Lint"
  out=$(bash -c "$LINT" 2>&1) || { echo "$out" | tail -25; echo "ERROR: lint"; fail=1; }
fi

if [ -n "$TEST" ]; then
  extra=""
  if [ "$(uname -s)" != "Darwin" ] && [ -n "$TEST_ARGS_NOT_MACOS" ]; then extra=" $TEST_ARGS_NOT_MACOS"; fi
  echo "== Tests${extra:+ (not macOS:$extra)}"
  out=$(bash -c "$TEST$extra" 2>&1) || { echo "$out" | tail -30; echo "ERROR: tests"; fail=1; }
else
  echo "== Tests: none configured"
fi

if [ $fail -eq 0 ]; then echo "OK"; else echo "FAILED"; fi
exit $fail
