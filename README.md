# HELLFIRE AI Solutions — Office Agent

Module 2. Email triage and drafted replies to routine requests, internal knowledge base (HELLFIRE + TETA+PI documentation) with search, document-workflow automation (contracts, client offers).

**Dogfooding:** first serves HELLFIRE/TETA+PI's own internal processes (Stage 1). Then an office-agent template gets extracted, pluggable into a client's Gmail/Outlook + internal knowledge repository (Stage 2).

## Technical decisions (locked 2026-07-20, details: `docs/architecture.md`)

- **Knowledge base:** lexical BM25 search (`office_agent/knowledge_base/`), no vector DB and no API key — rag-01 (session 07) didn't have a pipeline yet, so nothing to duplicate, and the backend can be swapped later without changing the `search()` interface.
- **LLM:** Anthropic API (`office_agent/llm.py`), optional and lazy-imported — kb search and rule-based triage work with zero API key. Draft replies without an LLM fall back to a template with raw KB excerpts, clearly marked `[DRAFT]`.
- **Email triage:** deterministic keyword classifier, 6 categories. A draft is generated only for `routine_question` — everything else (sales, billing, escalation, spam, unclassified) goes to a human with no draft. Nothing is ever sent automatically.
- **Inbox connector:** a real IMAP connector (`IMAPSource`) for a single HELLFIRE mailbox — not a generic multi-tenant OAuth (that's Stage 2). The domain `hellfiresol.com` is already live (DNS+SSL), but no mailbox has been provisioned on it yet — details in `docs/demo-ready-criteria.md`.
- **Docgen:** Jinja2 templates (`office_agent/docgen/`), fields matching `internal-db`'s `crm.clients`/`crm.contracts` schema so a DB row can be passed straight in without a translation layer.

## Quick start

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env  # optional: ANTHROPIC_API_KEY, OFFICE_AGENT_IMAP_*

office-agent kb search "EU data residency DSGVO"
office-agent triage run                              # fixture inbox, no credentials
office-agent triage run --source imap --use-llm       # real mail + LLM drafts (needs .env)
office-agent docgen offer --data samples/offer_example.json --out out/offer.md
```

`pytest tests/` — 21 tests, covering BM25 ranking, all 6 triage categories, draft grounding, IMAP message parsing (fake connection), and docgen validation/rendering.

## Status

Stage 1 — code ready and tested offline (fixtures in `samples/`). Blocked not on code, but on Bob: real IMAP (domain `hellfiresol.com` already live, waiting on a mailbox) and `ANTHROPIC_API_KEY` (deliberately deferred). Details and demo-ready criteria: `docs/demo-ready-criteria.md`.

**License:** MIT.
