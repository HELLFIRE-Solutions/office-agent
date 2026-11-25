from __future__ import annotations

from office_agent.email_triage.classifier import classify, is_draftable
from office_agent.email_triage.drafting import draft_reply
from office_agent.email_triage.models import TriageResult
from office_agent.email_triage.sources import EmailSource
from office_agent.knowledge_base.index import BM25Index
from office_agent.llm import LLMClient


def run_triage(
    source: EmailSource,
    kb_index: BM25Index | None = None,
    llm: LLMClient | None = None,
) -> list[TriageResult]:
    results = []
    for email in source.fetch():
        result = classify(email)
        if is_draftable(result.category) and kb_index is not None:
            result.draft_reply, result.kb_sources = draft_reply(email, kb_index, llm=llm)
        results.append(result)
    return results
