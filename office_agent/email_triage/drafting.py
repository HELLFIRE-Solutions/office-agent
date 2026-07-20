"""Draft replies for routine questions, grounded in the knowledge base.

Every draft is written for a human to review before sending — see
business-model.md's "sales always goes through a human" / no-self-serve
constraint, which this module treats as applying to all outbound mail,
not just sales. Nothing in this package sends email.
"""

from __future__ import annotations

from office_agent.email_triage.models import Email
from office_agent.knowledge_base.index import BM25Index
from office_agent.llm import LLMClient

SYSTEM_PROMPT = (
    "You are drafting a reply on behalf of HELLFIRE AI Solutions to a routine "
    "customer email. Use only the provided knowledge base excerpts as factual "
    "grounding. If the excerpts don't answer the question, say so plainly and "
    "note that a team member will follow up — never invent facts. Keep the tone "
    "professional and concise. This draft will be reviewed by a human before "
    "it is sent, so it's fine to leave notes in [brackets] for the reviewer."
)

NO_LLM_TEMPLATE = """[DRAFT — no LLM configured, review and rewrite before sending]

Hi,

Thanks for reaching out. Based on our internal docs, here's what's relevant
to your question:

{excerpts}

Best,
HELLFIRE AI Solutions
"""


def _format_excerpts(index: BM25Index, query: str, top_k: int) -> tuple[str, list[str]]:
    results = index.search(query, top_k=top_k)
    if not results:
        return "(no matching knowledge base entries found)", []

    lines = []
    sources = []
    for r in results:
        heading = f" — {r.chunk.heading}" if r.chunk.heading else ""
        lines.append(f"[{r.chunk.source}{heading}]\n{r.chunk.text}")
        sources.append(r.chunk.source)
    return "\n\n".join(lines), sources


def draft_reply(
    email: Email,
    index: BM25Index,
    llm: LLMClient | None = None,
    top_k: int = 3,
) -> tuple[str, list[str]]:
    """Returns (draft_text, kb_sources_used)."""
    query = f"{email.subject}\n{email.body}"
    excerpts, sources = _format_excerpts(index, query, top_k)

    if llm is None:
        return NO_LLM_TEMPLATE.format(excerpts=excerpts), sources

    prompt = (
        f"Customer email:\nFrom: {email.sender}\nSubject: {email.subject}\n\n{email.body}\n\n"
        f"Knowledge base excerpts:\n{excerpts}\n\n"
        "Write the reply."
    )
    return llm.complete(SYSTEM_PROMPT, prompt), sources
