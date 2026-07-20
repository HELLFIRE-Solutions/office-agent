"""Rule-based email classification.

Deliberately rule-based rather than LLM-only for Stage 1: it's
deterministic, testable offline, and costs nothing per email. An LLM
classifier can be plugged in later (see office_agent.llm) for the cases
these keyword rules leave as UNCLASSIFIED — but UNCLASSIFIED already
routes to a human, so there's no correctness gap, only a triage-speed one.

Rule order matters: first match wins. Sales/billing/escalation keywords
are checked before the routine-question fallback so a message that
mentions both (e.g. "pricing for support ticket") still routes to a
human rather than getting an auto-draft.
"""

from __future__ import annotations

import re

from office_agent.email_triage.models import AUTO_DRAFTABLE, REQUIRES_HUMAN, Category, Email, TriageResult

_RULES: list[tuple[str, Category, re.Pattern[str]]] = [
    (
        "spam_unsubscribe",
        Category.SPAM,
        re.compile(r"\b(unsubscribe|viagra|lottery|winning ticket|crypto giveaway)\b", re.IGNORECASE),
    ),
    (
        "sales_inbound",
        Category.SALES_LEAD,
        re.compile(
            r"\b(pricing|quote|demo|proposal|interested in|purchase|buy|sales|partnership)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "billing",
        Category.BILLING,
        re.compile(r"\b(invoice|payment|billing|refund|overdue|receipt)\b", re.IGNORECASE),
    ),
    (
        "support_escalation",
        Category.SUPPORT_ESCALATION,
        re.compile(r"\b(urgent|down|broken|outage|incident|not working|critical|escalat)\b", re.IGNORECASE),
    ),
    (
        "routine_question",
        Category.ROUTINE_QUESTION,
        re.compile(
            r"\b(how do i|how does|what is|where can i|documentation|docs|question about|"
            r"could you explain|can you tell me)\b",
            re.IGNORECASE,
        ),
    ),
]


def classify(email: Email) -> TriageResult:
    haystack = f"{email.subject}\n{email.body}"
    for rule_name, category, pattern in _RULES:
        if pattern.search(haystack):
            return TriageResult(
                email=email,
                category=category,
                matched_rule=rule_name,
                requires_human=category in REQUIRES_HUMAN,
            )

    return TriageResult(
        email=email,
        category=Category.UNCLASSIFIED,
        matched_rule=None,
        requires_human=True,
    )


def is_draftable(category: Category) -> bool:
    return category in AUTO_DRAFTABLE
