"""Exercise 7 (step 8): offline results are not product outcomes.

candidate-v2 passed every offline case. Did it help agents? Read the ILLUSTRATIVE
pilot data in data/pilot/pilot_tickets.ILLUSTRATIVE.csv. Each row is a dict
with string values; handling_minutes is a number as text, e.g. "6".

    python3 -m exercises 7
"""


def median_minutes(rows: list[dict], arm: str, request_type: str | None = None) -> tuple[float, int]:
    """Median handling_minutes for one arm ("manual" or "assisted"), optionally
    for one request_type. Return (median, number_of_tickets)."""
    raise NotImplementedError("implement median_minutes()")


def rate(rows: list[dict], arm: str, column: str, value: str) -> tuple[int, int]:
    """In one arm, how many rows have row[column] == value? Return (count, rows_in_arm)."""
    raise NotImplementedError("implement rate()")


# In two or three sentences: why doesn't "26 / 26 offline" prove that handling
# time or customer outcomes improved? Replace the TODO.
WHY_OFFLINE_IS_NOT_ENOUGH = "TODO"
