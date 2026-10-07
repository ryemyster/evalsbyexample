#!/usr/bin/env bash
# Simulates a learner's first clone: commits the working tree (respecting
# .gitignore) into a throwaway repository, clones it into an empty directory,
# and runs the README commands there, including the regression-case walkthrough.
# Nothing in this folder is changed. Usage: bash scripts/verify_fresh_clone.sh
set -euo pipefail
SRC="$(cd "$(dirname "$0")/.." && pwd)"
PY="${PYTHON:-python3}"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

mkdir "$WORK/origin"
if [[ -d "$SRC/.git" ]]; then
  git -C "$SRC" ls-files -co --exclude-standard | (cd "$SRC" && tar -cf - -T -) | (cd "$WORK/origin" && tar -xf -)
else
  (cd "$SRC" && tar -cf - --exclude ./runs --exclude ./.git .) | (cd "$WORK/origin" && tar -xf -)
fi
cd "$WORK/origin"
git init -q
git add -A
git -c user.name=verify -c user.email=verify@example.com commit -qm "snapshot"
echo "Files a learner would clone: $(git ls-files | wc -l | tr -d ' ')"
git ls-files | grep -E '^runs/.+\.json$' && { echo "FAILED: run files would be committed"; exit 1; } || true

git clone -q "$WORK/origin" "$WORK/clone"
cd "$WORK/clone"
echo "Using $("$PY" --version)"
"$PY" -m returns_eval start | grep -qF "changes can be undone" && echo "ok: start finds the clone ready"
PYTHON="$PY" bash scripts/verify_readme_commands.sh

echo
echo "== Regression walkthrough (README: Add the failure as a regression case)"
"$PY" -c "import json; json.dump(json.loads(open('solutions/ex08_regression_case.jsonl').readline()), open('rc027.json','w'), indent=2)"
"$PY" -m returns_eval add-case rc027.json
# Same edit the README asks for: bump the top-level version and add a changelog line.
"$PY" - <<'PYEOF'
import json
path = "data/cases/manifest.json"
m = json.load(open(path))
m["version"] = "1.1"
m["changelog"].append({"version": "1.1", "date": "2026-08-27", "change": "Add RC-027 from pilot incident PI-001."})
json.dump(m, open(path, "w"), indent=2)
PYEOF
out="$("$PY" -m returns_eval run --candidate candidate-v2)"
grep -qF "CASES PASSED: 26 / 27 (96%)" <<<"$out" && grep -qF "DECISION: NOT READY" <<<"$out" || { echo "$out"; exit 1; }
echo "ok: candidate-v2 fails RC-027 and is NOT READY"
"$PY" -m exercises 8 >/dev/null && echo "ok: Exercise 8 passes once RC-027 is added and the version bumped"
cp solutions/ex09_candidate_v3.py exercises/ex09_candidate_v3.py
out="$("$PY" -m returns_eval run --candidate exercises.ex09_candidate_v3:CandidateV3 --baseline baseline)"
grep -qF "CASES PASSED: 27 / 27 (100%)" <<<"$out" || { echo "$out"; exit 1; }
echo "ok: the Exercise 9 fix passes all 27 cases"
"$PY" -m unittest discover -s tests -t . 2>&1 | tail -1

echo
echo "== Start over (README: Start over)"
echo "# my experiment" >> playground/my_candidate.py
"$PY" -m returns_eval reset
"$PY" -m returns_eval reset --all --yes
rm -f rc027.json
leftover="$(git status --porcelain)"
[[ -z "$leftover" ]] || { echo "FAILED: not back to the clone after reset --all:"; echo "$leftover"; exit 1; }
echo "ok: reset --all returned every tracked file to the clone; backups kept in backups/"
grep -qF "# my experiment" backups/*/playground/my_candidate.py && echo "ok: the experiment is in backups/"
out="$("$PY" -m returns_eval compare baseline candidate-v1 candidate-v2)"
grep -qF "26 / 26 (100%)" <<<"$out" || { echo "$out"; exit 1; }
echo "ok: rebuilt the standard comparison after reset"
echo
echo "Fresh clone verified."
