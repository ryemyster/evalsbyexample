#!/usr/bin/env bash
# Runs the README's commands in order and checks the key results.
# Only writes to runs/ (ignored by git). Usage: bash scripts/verify_readme_commands.sh
# Set PYTHON to test a specific interpreter, e.g. PYTHON=/usr/bin/python3 (macOS's built-in 3.9).
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PYTHON:-python3}"

step() { printf '\n== %s\n' "$*"; }
expect() {  # expect "<text that must appear>" command args...
  local want="$1"; shift
  local out
  out="$("$@" 2>&1)" || { local code=$?; if [[ $code -ne 1 ]]; then echo "$out"; echo "FAILED (exit $code): $*"; exit 1; fi; }
  if ! grep -qF -- "$want" <<<"$out"; then
    echo "$out" | tail -30
    echo "FAILED: expected to see: $want"
    echo "  from: $*"
    exit 1
  fi
  echo "ok: $* -> \"$want\""
}

step "Python version"
"$PY" -c 'import sys; assert sys.version_info >= (3, 9), sys.version; print(sys.version.split()[0])'

step "Clone to first result"
expect "Ready." "$PY" -m returns_eval start --no-save
expect "26 of 26 cases" "$PY" -m returns_eval cases
expect "DECISION: BLOCKED" "$PY" -m returns_eval run --candidate candidate-v1
expect "CASES PASSED: 13 / 26 (50%)" "$PY" -m returns_eval report latest:candidate-v1

step "One case, start to finish"
expect "Ana Reyes (C-2001, ana.reyes@example.com)" "$PY" -m returns_eval show-case RC-001
expect "RESULT: FAIL (worst severity: critical)" "$PY" -m returns_eval report latest:candidate-v1 --case RC-001

step "Inspect, change, rerun"
expect "newly failing (2): RC-024 [critical], RC-025 [critical]" "$PY" -m returns_eval compare baseline candidate-v1
expect "issue_refund(order_id='EO-10824', amount='199.00')" "$PY" -m returns_eval report latest:candidate-v1 --case RC-024
expect "26 / 26 (100%)" "$PY" -m returns_eval compare baseline candidate-v1 candidate-v2
expect "DECISION: PENDING" "$PY" -m returns_eval run --candidate candidate-v2 --baseline baseline
expect "usability                  23 / 26 (88%)" "$PY" -m returns_eval review-summary latest:candidate-v2 data/human_review/candidate-v2.reviewer-a.ILLUSTRATIVE.csv data/human_review/candidate-v2.reviewer-b.ILLUSTRATIVE.csv
expect "DECISION: READY FOR A SUPERVISED PILOT" "$PY" -m returns_eval run --candidate candidate-v2 --baseline baseline --review data/human_review/candidate-v2.reviewer-a.ILLUSTRATIVE.csv data/human_review/candidate-v2.reviewer-b.ILLUSTRATIVE.csv

expect "**READY FOR A SUPERVISED PILOT.**" "$PY" -m returns_eval brief baseline candidate-v2 --review data/human_review/candidate-v2.reviewer-a.ILLUSTRATIVE.csv data/human_review/candidate-v2.reviewer-b.ILLUSTRATIVE.csv
expect "Escalation recall" "$PY" -m returns_eval compare baseline candidate-v1

step "Pilot"
expect "ILLUSTRATIVE DATA" "$PY" -m returns_eval pilot

step "Other commands"
expect "candidate-v2" "$PY" -m returns_eval candidates
expect "Wrote 26 drafts" "$PY" -m returns_eval review-sheet latest:candidate-v2 --reviewer readme-check

step "Make it your own"
expect "CASES PASSED: 26 / 26 (100%)" "$PY" -m returns_eval run --candidate playground.my_candidate:MyCandidate --baseline baseline
expect "RC-900 PASS" "$PY" -m returns_eval run --candidate candidate-v2 --cases playground/my_case.json
expect "DECISION: BLOCKED" "$PY" -m returns_eval run --candidate playground.my_model:OfflineFakeModel
expect "likely setup, not the model" env -u EVALS_MODEL "$PY" -m returns_eval run --candidate playground.my_model:OpenAIModel --only RC-001 RC-024
expect "EXTEND HERE" grep -rn "EXTEND HERE" returns_eval

step "Start over"
expect "Deleted" "$PY" -m returns_eval clean --reviews
expect "reset" "$PY" -m returns_eval reset
expect "26 / 26 (100%)" "$PY" -m returns_eval compare baseline candidate-v1 candidate-v2

step "Exercises and tests"
expect "4 / 4 tests passed" "$PY" -m exercises 4 --solution
expect "not done yet" "$PY" -m exercises 3
"$PY" -m exercises all --solution
"$PY" -m unittest discover -s tests -t .

printf '\nAll README commands behaved as documented.\n'
