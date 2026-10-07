from ._support import ExerciseCase, load

PROMISES = [
    "Your refund will arrive within 5 days.",
    "You'll see the refund in 3 business days.",
    "Refunds usually take 5-7 business days.",
    "We'll send your refund by Friday.",
    "Your refund will be issued by August 20.",
    "We will refund you today.",
    "You'll be refunded tomorrow.",
]
NOT_PROMISES = [
    "You can return items within 30 days of delivery.",
    "Refunds begin after inspection, and we can't promise an exact date.",
    "Your return label expires in 14 days.",
    "We received your return on August 7.",
    "Today is the last day to start your return.",
]


class TestEx03(ExerciseCase):
    exercise = 3
    where = "exercises/ex03_refund_timing_check.py"

    def setUp(self):
        self.find = load("ex03_refund_timing_check").find_refund_timing_promises

    def test_flags_each_promise(self):
        for sentence in PROMISES:
            found = self.call(self.find, sentence)
            self.assertEqual(found, [sentence], f"should flag: {sentence!r}")

    def test_ignores_non_promises(self):
        for sentence in NOT_PROMISES:
            found = self.call(self.find, sentence)
            self.assertEqual(found, [], f"should not flag: {sentence!r} (no refund timing promised)")

    def test_follow_on_sentence(self):
        text = "Your refund has been approved. It should appear within 5-7 business days."
        self.assertEqual(self.call(self.find, text), ["It should appear within 5-7 business days."],
                         "a sentence starting with 'It' right after a refund sentence is about the refund")

    def test_returns_only_matching_sentences_in_order(self):
        text = ("Thanks for your patience. Your refund goes to your original card within 3 days. "
                "Return labels expire in 14 days. You'll get the refund by Monday.")
        self.assertEqual(self.call(self.find, text),
                         ["Your refund goes to your original card within 3 days.", "You'll get the refund by Monday."])

    def test_agrees_with_candidate_drafts(self):
        v1_draft = ("Hi Ana, good news: we received your return on August 7 and your refund of $89.00 has "
                    "been issued. It should appear within 5-7 business days.")
        v2_draft = ("Hi Ana, we received your return on August 7, and it's now waiting for inspection. Once it "
                    "passes, your refund goes back to your original payment method. I can't give you an exact "
                    "date, but you'll get an email as soon as the refund is issued.")
        self.assertEqual(len(self.call(self.find, v1_draft)), 1, "candidate-v1's RC-001 draft promises timing")
        self.assertEqual(self.call(self.find, v2_draft), [], "candidate-v2's RC-001 draft makes no timing promise")
