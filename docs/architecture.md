# office-agent — Architecture Decisions (Session 06, Stage 1)

Status: decided in this session (2026-07-20).

## 1. Knowledge base retrieval: BM25 now, not rag-01's embedding pipeline

**Decision: pure-Python lexical BM25 search (`office_agent/knowledge_base/`), no vector DB, no embeddings API.**

Rationale:
- The kickoff prompt for this session says to coordinate with rag-01 (session 07) rather than duplicate its pipeline from scratch — but rag-01 is still an unstarted scaffold (README + LICENSE only, no ingest/index code, vector DB choice between Qdrant/pgvector still open) as of this session. There is nothing to depend on yet.
- Rather than block Stage 1 on rag-01, or build a throwaway embeddings pipeline that would just get replaced, this module implements the smallest thing that's genuinely useful today: BM25 lexical search over the HELLFIRE/TETA+PI doc corpus. Zero external dependencies, zero API key, zero network call, works offline, and is good enough for a small (tens-to-low-hundreds of documents) internal corpus.
- The interface is deliberately narrow and stable: `ingest_directory(path) -> RawChunk[]`, `BM25Index.from_raw_chunks(...)`, `index.search(query, top_k)`. When rag-01 ships an embedding index worth depending on, swap the implementation behind this interface — `email_triage.drafting` and the CLI only touch `BM25Index.search()`, so the swap shouldn't ripple outward.
- Chunking strategy (Markdown heading split, then paragraph split with a max-chars cap) lives in `knowledge_base/ingest.py`, separated from the index itself, so it can also be reused as-is if/when the retrieval backend changes.

Revisit if: the corpus grows large enough that lexical search misses paraphrased queries often enough to hurt the triage draft quality, or once rag-01 has a working embedding index and vector DB decision locked in — coordinate with that session before rebuilding this one.

## 2. LLM stack: Anthropic API, optional and lazily imported

**Decision: `office_agent/llm.py` wraps the Anthropic Python SDK, imported only when a draft actually needs an LLM call.**

Rationale:
- Same reasoning as gtm-agent (session 05): dogfoods the stack HELLFIRE sells, thin dependency (`anthropic` is an optional extra in `pyproject.toml`, not a base dependency).
- kb search and rule-based triage classification work with zero API key and zero network access — only `email_triage.drafting.draft_reply()` needs an `LLMClient`, and even that degrades to a template-based draft (raw KB excerpts, clearly marked `[DRAFT — no LLM configured]`) when no LLM is passed, so the CLI is usable out of the box.
- Model default is `claude-sonnet-5`— good default balance of quality/cost for internal drafting; can be overridden via `AnthropicClient(model=...)`.

Blocked on: a real `ANTHROPIC_API_KEY` for HELLFIRE's own usage (not created in this session — no account access). `office_agent/llm.py` and `email_triage/drafting.py` are code-complete and safe to run once the key is set in `.env` (see `.env.example`); `office-agent triage run --use-llm` exercises this path.

## 3. Email triage: rule-based classification, human-reviewed drafts only

**Decision: deterministic keyword-rule classifier (`email_triage/classifier.py`) decides the category; only `ROUTINE_QUESTION` gets an auto-drafted reply, and every draft is written to be reviewed by a human before sending — this module never sends email.**

Rationale:
- Matches the business-model constraint that sales always goes through a human and there's no self-serve path (`samples/docs/business-model.md`) — extended here to *all* outbound mail, not just sales, since Stage 1 has no send capability at all yet and a wrong auto-reply is a worse failure mode than a slower one.
- Categories (`SALES_LEAD`, `ROUTINE_QUESTION`, `SUPPORT_ESCALATION`, `BILLING`, `SPAM`, `UNCLASSIFIED`) are deliberately coarse and rule-based rather than LLM-classified: deterministic, testable offline, and free per email. `UNCLASSIFIED` is the safe default for anything the rules don't recognize — it always routes to a human, so there's no silent misrouting, only a triage-speed cost for ambiguous mail. An LLM-based classifier can be layered in later for the `UNCLASSIFIED` bucket specifically, without touching the rest of the pipeline.
- Rule order matters and is tested: sales/billing/escalation/spam keywords are checked before the routine-question fallback, so a message mentioning both routes to a human rather than getting auto-drafted (see `tests/test_email_triage.py`).

## 4. Inbox connector: real IMAP for HELLFIRE's own mailbox, not a generic Gmail/Outlook connector yet

**Decision: `email_triage/sources.py` implements a real `IMAPSource` (stdlib `imaplib` + `email`, IMAP4_SSL) against a single hardcoded mailbox via env vars — not a per-client, multi-tenant OAuth connector.**

Rationale:
- The kickoff prompt's Stage 1/Stage 2 split is explicit: Stage 1 is HELLFIRE using this internally; Stage 2 is the client-facing template that connects to *a client's* Gmail/Outlook. Building OAuth app registration, token refresh, and multi-provider abstraction now would be Stage 2 work done early, for a problem Stage 1 doesn't have (one mailbox, one owner).
- `IMAPSource` is code-complete and unit-tested against a fake IMAP connection (`tests/test_imap_source.py`) but needs `OFFICE_AGENT_IMAP_HOST/USER/PASSWORD` (e.g. a Gmail app password) in `.env` to hit a real inbox — not provisioned in this session, same "code-complete but credential-blocked" status as gtm-agent's HubSpot/SMTP integrations.
- `JSONFileSource` remains the default and is what the test suite and `--source json` (CLI default) use — no live credentials required to verify the pipeline works end-to-end.

## 5. Document generation: Jinja2 templates matching internal-db's schema

**Decision: `office_agent/docgen/` renders Markdown (not PDF/docx yet) from data dicts whose field names mirror `crm.clients` / `crm.contracts` in `internal-db`.**

Rationale:
- `internal-db` (session 04) already has a real schema for clients, contacts, and contracts (module vs. people, fixed price vs. tier+monthly rate, EUR default currency). Reusing those exact field names (`legal_name`, `contract_type`, `fixed_price`, `people_tier`, `monthly_rate`, ...) means a future integration can pass a DB row straight into `render_offer()`/`render_contract()` with no translation layer, and `generate.py`'s validation (`REQUIRED_MODULE_FIELDS`, `REQUIRED_PEOPLE_FIELDS`, the `people_tier` enum check) mirrors the DB's `chk_contract_shape` CHECK constraint.
- Output is Markdown, not PDF/docx: every generated document is explicitly a draft for human sign-off ("This offer requires sign-off from a HELLFIRE team member before it is considered final" is baked into the template), so a polished final format isn't Stage 1's bottleneck — reviewability is. PDF/docx rendering is a small addition later (e.g. via `pandoc` or `python-docx`) if/when it's actually needed for sending to a client.

## Summary for Session Manager

Stage 1 is code-complete and tested (21 passing tests, `office-agent` CLI installable via `pip install -e .`) using offline fixtures (`samples/docs/`, `samples/inbox/sample_inbox.json`, `samples/offer_example.json`) — no external credentials required to verify it works. Two things are genuinely blocked on Bob, not on more coding: an `ANTHROPIC_API_KEY` (for LLM-drafted replies instead of the raw-excerpt fallback) and `OFFICE_AGENT_IMAP_*` credentials (an app password for HELLFIRE's real inbox, to triage real mail instead of the fixture). See `docs/demo-ready-criteria.md`.
