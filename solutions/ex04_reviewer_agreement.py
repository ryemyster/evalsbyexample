"""Reference solution for Exercise 4."""


def _matched(reviews_a, reviews_b):
    b_by_key = {(r["case_id"], r["draft_fingerprint"]): r for r in reviews_b}
    for a in reviews_a:
        b = b_by_key.get((a["case_id"], a["draft_fingerprint"]))
        if b is not None:
            yield a, b


def percent_agreement(reviews_a, reviews_b, criterion):
    pairs = list(_matched(reviews_a, reviews_b))
    return sum(a[criterion] == b[criterion] for a, b in pairs), len(pairs)


def disagreements(reviews_a, reviews_b, criterion):
    return sorted(a["case_id"] for a, b in _matched(reviews_a, reviews_b) if a[criterion] != b[criterion])
