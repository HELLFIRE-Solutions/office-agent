from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Category(str, Enum):
    SALES_LEAD = "sales_lead"
    ROUTINE_QUESTION = "routine_question"
    SUPPORT_ESCALATION = "support_escalation"
    BILLING = "billing"
    SPAM = "spam"
    UNCLASSIFIED = "unclassified"


# Sales always goes through a human (no self-serve) — see business-model.md.
# Only routine questions get an auto-drafted reply; everything else is
# routed to a human with no draft generated, so there's nothing to
# accidentally auto-send.
AUTO_DRAFTABLE = {Category.ROUTINE_QUESTION}

REQUIRES_HUMAN = {
    Category.SALES_LEAD,
    Category.SUPPORT_ESCALATION,
    Category.BILLING,
    Category.UNCLASSIFIED,
}


@dataclass
class Email:
    id: str
    sender: str
    subject: str
    body: str


@dataclass
class TriageResult:
    email: Email
    category: Category
    matched_rule: str | None
    requires_human: bool
    draft_reply: str | None = None
    kb_sources: list[str] | None = None
