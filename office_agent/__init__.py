"""HELLFIRE AI Office — internal dogfooding module (Stage 1).

Three pieces, usable independently or via the CLI:
- office_agent.knowledge_base: search over internal docs (BM25, no external deps)
- office_agent.email_triage: classify inbound email, draft routine replies
- office_agent.docgen: render contracts/offers from templates
"""

__version__ = "0.1.0"
