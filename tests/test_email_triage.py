from office_agent.email_triage.classifier import classify, is_draftable
from office_agent.email_triage.drafting import draft_reply
from office_agent.email_triage.models import Category, Email
from office_agent.email_triage.pipeline import run_triage
from office_agent.email_triage.sources import JSONFileSource
from office_agent.knowledge_base.index import BM25Index
from office_agent.knowledge_base.ingest import ingest_directory

SAMPLE_INBOX = "samples/inbox/sample_inbox.json"
SAMPLE_DOCS_DIR = "samples/docs"


def _email(subject: str, body: str = "") -> Email:
    return Email(id="1", sender="a@example.com", subject=subject, body=body)


def test_sales_email_routes_to_human_not_draftable():
    result = classify(_email("Interested in pricing and a demo"))
    assert result.category == Category.SALES_LEAD
    assert result.requires_human is True
    assert is_draftable(result.category) is False


def test_billing_email_requires_human():
    result = classify(_email("Overdue invoice", "please confirm payment"))
    assert result.category == Category.BILLING
    assert result.requires_human is True


def test_urgent_escalation_requires_human():
    result = classify(_email("URGENT production down"))
    assert result.category == Category.SUPPORT_ESCALATION
    assert result.requires_human is True


def test_spam_detected():
    result = classify(_email("winning ticket", "click unsubscribe now"))
    assert result.category == Category.SPAM


def test_routine_question_is_draftable():
    result = classify(_email("Question about documentation", "How do I use the knowledge base search?"))
    assert result.category == Category.ROUTINE_QUESTION
    assert result.requires_human is False
    assert is_draftable(result.category) is True


def test_unclassified_defaults_to_human():
    result = classify(_email("hey", "just wanted to say hi"))
    assert result.category == Category.UNCLASSIFIED
    assert result.requires_human is True


def test_draft_reply_uses_kb_and_never_sends():
    index = BM25Index.from_raw_chunks(ingest_directory(SAMPLE_DOCS_DIR))
    email = _email("Question about DSGVO", "Does hosting meet EU data residency requirements?")
    draft, sources = draft_reply(email, index, llm=None)
    assert "DRAFT" in draft
    assert sources
    assert "business-model.md" in sources[0]


def test_pipeline_only_drafts_routine_questions():
    source = JSONFileSource(SAMPLE_INBOX)
    index = BM25Index.from_raw_chunks(ingest_directory(SAMPLE_DOCS_DIR))
    results = run_triage(source, kb_index=index, llm=None)

    by_category = {r.category for r in results}
    assert Category.SALES_LEAD in by_category
    assert Category.SPAM in by_category

    for r in results:
        if r.category == Category.ROUTINE_QUESTION:
            assert r.draft_reply is not None
        else:
            assert r.draft_reply is None
