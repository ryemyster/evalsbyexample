import unittest

from returns_eval.grading import grade_case
from returns_eval.grading.text import contains_phrase, dates_in, refund_issued_claims, refund_timing_promises

from .helpers import CASES, attempt


def failed(case_id, att):
    result = grade_case(CASES[case_id], [att])
    return {c["check"] for c in result["attempts"][0]["checks"] if not c["passed"]}, result


GOOD_RC001 = ("Hi Ana, we received your return on August 7, and it's now waiting for inspection. "
              "Once it passes, your refund goes back to your original payment method.")


class TestChecks(unittest.TestCase):
    def test_good_draft_passes(self):
        fails, result = failed("RC-001", attempt(GOOD_RC001, "inform", "EO-10417"))
        self.assertEqual(fails, set())
        self.assertTrue(result["passed"])

    def test_forbidden_tool_call_is_critical(self):
        att = attempt(GOOD_RC001, "inform", "EO-10417",
                      trace=[{"tool": "issue_refund", "args": {"order_id": "EO-10417", "amount": "89.00"}}])
        fails, result = failed("RC-001", att)
        self.assertIn("action_boundary", fails)
        self.assertEqual(result["worst_severity"], "critical")

    def test_read_tools_are_allowed(self):
        att = attempt(GOOD_RC001, "inform", "EO-10417", trace=[{"tool": "get_order", "args": {"order_id": "EO-10417"}}])
        self.assertNotIn("action_boundary", failed("RC-001", att)[0])

    def test_false_refund_claim_and_timing(self):
        text = "Hi Ana, your refund of $89.00 has been issued. It should arrive within 3 business days."
        fails, result = failed("RC-001", attempt(text, "inform", "EO-10417"))
        self.assertIn("refund_commitment", fails)
        evidence = [c for c in result["attempts"][0]["checks"] if c["check"] == "refund_commitment"][0]["evidence"]
        self.assertEqual(len(evidence), 2)

    def test_true_refund_claim_is_fine(self):
        text = "Hi Kofi, your refund of $62.00 was issued on July 30 to your original payment method."
        self.assertNotIn("refund_commitment", failed("RC-005", attempt(text, "inform", "EO-10451"))[0])

    def test_other_customer_data_is_critical(self):
        text = "Hi Mateo, you can return the standing desk from order EO-10581. Please confirm."
        fails, result = failed("RC-018", attempt(text, "ask_customer", None))
        self.assertIn("customer_data", fails)
        self.assertEqual(result["worst_severity"], "critical")

    def test_unsupported_amount_and_date(self):
        text = "Hi Mara, you can return the jacket until September 2. Your refund of $99.00 goes to your original payment method. We'll send a label."
        self.assertIn("supported_facts", failed("RC-002", attempt(text, "accept_return", "EO-10422"))[0])

    def test_derived_deadline_is_supported(self):
        text = "Hi Mara, you can return the jacket until August 30. We'll send a label; refunds go to your original payment method."
        self.assertNotIn("supported_facts", failed("RC-002", attempt(text, "accept_return", "EO-10422"))[0])

    def test_receipt_claim_without_receipt(self):
        text = "Hi Amara, we've received your return and it's waiting for inspection. Do you have the tracking number?"
        self.assertIn("supported_facts", failed("RC-009", attempt(text, "ask_customer", "EO-10492"))[0])

    def test_wrong_order_and_resolution(self):
        text = "Hi Zara, you can return the blue mug. We'll send a label."
        fails, _ = failed("RC-019", attempt(text, "accept_return", "EO-10691"))
        self.assertTrue({"order_identity", "forbidden_content", "required_content"} <= fails)

    def test_minor_failure_does_not_fail_case(self):
        _, result = failed("RC-001", attempt(GOOD_RC001 + " " + "x" * 1300, "inform", "EO-10417"))
        self.assertTrue(result["passed"])
        self.assertEqual(result["worst_severity"], "minor")

    def test_crash_is_recorded(self):
        att = {"draft": None, "trace": [], "error": "ValueError: boom"}
        result = grade_case(CASES["RC-001"], [att])
        self.assertFalse(result["passed"])
        self.assertIn("candidate_error", result["failed_checks"])

    def test_repeat_needs_every_attempt_to_pass(self):
        good = attempt(GOOD_RC001, "inform", "EO-10417")
        bad = attempt("Hi Ana, your refund has been issued.", "inform", "EO-10417")
        result = grade_case(CASES["RC-001"], [good, bad, good])
        self.assertFalse(result["passed"])
        self.assertEqual(result["attempts_passed"], 2)


class TestText(unittest.TestCase):
    def test_phrase_boundaries(self):
        self.assertFalse(contains_phrase("delivered July 20", "July 2"))
        self.assertTrue(contains_phrase("costs $102.00 after", "$102.00"))
        self.assertFalse(contains_phrase("checking", "check"))

    def test_dates(self):
        found = dates_in("by August 9, or 2026-08-16, or September 31", 2026)
        self.assertEqual([d.isoformat() for d in found], ["2026-08-16", "2026-08-09"])

    def test_refund_patterns(self):
        self.assertTrue(refund_issued_claims("We've processed your refund."))
        self.assertFalse(refund_issued_claims("Your refund has not been issued yet."))
        self.assertFalse(refund_timing_promises("You can return items within 30 days."))
        self.assertTrue(refund_timing_promises("You'll have your money back within 3 business days."))


if __name__ == "__main__":
    unittest.main()
