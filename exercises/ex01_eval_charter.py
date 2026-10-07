"""Exercise 1 (steps 1-3): write the eval charter before writing any code.

Replace every "TODO". Plain sentences are fine. Then run:

    python3 -m exercises 1

Guidance
- product_decision: the yes/no question this eval informs. Not "is the model good?"
- baseline: how the job gets done today, without the assistant.
- success: one list per level. Output quality and workflow behavior can be checked
  offline. Product outcomes need a pilot.
- unacceptable_failures: map each failure (in plain words) to the name of the check
  in returns_eval/grading/checks.py that would catch it. Every critical check
  should appear at least once.
"""

CHARTER = {
    "customer_job": "TODO: who is doing what job?",
    "product_decision": "TODO: the yes/no question, ending with a question mark",
    "baseline": "TODO: how is this done today?",
    "success": {
        "output_quality": ["TODO"],
        "workflow_behavior": ["TODO"],
        "product_outcome": ["TODO"],
    },
    "unacceptable_failures": {
        "TODO: describe a failure": "TODO: check name",
    },
}
