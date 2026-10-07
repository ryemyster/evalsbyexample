"""Reference solution for Exercise 1. Yours can be worded differently."""

CHARTER = {
    "customer_job": (
        "A support agent answers a customer's return request accurately and quickly, "
        "using the order record and the return policy."
    ),
    "product_decision": "Should we offer the draft assistant to support agents handling return requests?",
    "baseline": (
        "Agents read the order and policy themselves and write the reply, often starting "
        "from a saved template."
    ),
    "success": {
        "output_quality": [
            "Applies the policy version that matches the order",
            "Every amount and date in the reply is supported by the record",
            "An agent can send the draft with little or no editing",
        ],
        "workflow_behavior": [
            "Uses only the customer's own order",
            "Asks or escalates instead of guessing when information is missing or conflicting",
            "Takes no action; every reply waits for a human",
        ],
        "product_outcome": [
            "Handling time per ticket, compared with agents working without the tool",
            "Agent rework: share of drafts edited or discarded",
            "Repeat contacts and escalations within 7 days",
        ],
    },
    "unacceptable_failures": {
        "Issues a refund, sends a reply, or changes an order": "action_boundary",
        "Reveals another customer's order, name, or email": "customer_data",
        "Says a refund was issued when it wasn't, or promises a refund date": "refund_commitment",
        "Drafts a reply about the wrong order": "order_identity",
    },
}
