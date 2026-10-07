"""Run a candidate over cases, then hand the output to the grader.

The harness is the only code that sees both sides. It builds the request a
candidate is allowed to see, records the trace, and passes the raw output to
the grader. It does not judge anything itself.
"""

from __future__ import annotations

import json
import platform
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .candidates import Candidate
from .cases import REPO_ROOT, CaseSet, load_policy
from .grading import GRADER_VERSION, grade_case
from .models import Customer, Request
from .tools import Toolbox

RUNS_DIR = REPO_ROOT / "runs"
RUN_FORMAT = "1"


def build_request(case: dict[str, Any]) -> Request:
    return Request(customer=Customer(**case["customer"]), message=case["message"],
                   as_of=case["as_of"], policy=load_policy(case["policy_version"]))


def produce(candidate: Candidate, case: dict[str, Any]) -> dict[str, Any]:
    """One attempt: the draft (or the error) plus every tool call made."""
    tools = Toolbox(case["orders"])
    draft, error = None, None
    started = time.perf_counter()
    try:
        draft = candidate.draft_reply(build_request(case), tools).to_dict()
    except Exception as exc:  # a crash is a result to record, not a reason to stop the run
        last = traceback.extract_tb(exc.__traceback__)[-1]
        error = f"{type(exc).__name__}: {exc} (at {Path(last.filename).name}:{last.lineno})"
    seconds = round(time.perf_counter() - started, 3)
    return {"draft": draft, "trace": [c.to_dict() for c in tools.trace], "error": error, "seconds": seconds}


def run_eval(candidate: Candidate, case_set: CaseSet, repeat: int = 1) -> dict[str, Any]:
    started = datetime.now(timezone.utc).replace(microsecond=0)
    results = []
    for case in case_set.cases:
        attempts = [produce(candidate, case) for _ in range(repeat)]
        results.append(grade_case(case, attempts))
    meta = {
        "run_format": RUN_FORMAT,
        "run_id": f"{started:%Y%m%dT%H%M%SZ}_{candidate.name}",
        "run_time_utc": started.isoformat(),
        "candidate": candidate.name,
        "candidate_version": candidate.version,
        "candidate_description": candidate.description,
        "case_set_version": case_set.version,
        "case_set_sha256": case_set.sha256,
        "case_files": case_set.files,
        "case_count": len(case_set.cases),
        "policy_versions": sorted({c["policy_version"] for c in case_set.cases}),
        "grader_version": GRADER_VERSION,
        "repeat": repeat,
        "python": platform.python_version(),
    }
    return {"meta": meta, "results": results}


def save_run(run: dict[str, Any], out_dir: Path | None = None) -> Path:
    out_dir = Path(out_dir or RUNS_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{run['meta']['run_id']}.json"
    n = 1
    while path.exists():  # two runs in the same second
        n += 1
        path = out_dir / f"{run['meta']['run_id']}-{n}.json"
    path.write_text(json.dumps(run, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def load_run(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    if not path.exists():
        raise SystemExit(f"Run file not found: {path}")
    run = json.loads(path.read_text(encoding="utf-8"))
    if run.get("meta", {}).get("run_format") != RUN_FORMAT:
        raise SystemExit(f"{path} is not a run file this version can read.")
    return run
