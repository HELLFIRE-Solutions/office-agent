# Stage 1 — "Demo-ready" criteria (locked in with Bob, 2026-07-20)

Bob confirmed: real IMAP connectivity is the target, but deliberately sequenced *after* a branded HELLFIRE mailbox exists — he wants the real inbox to be on the HELLFIRE domain, not a placeholder address, before wiring live credentials. The domain itself (`hellfiresol.com`) is already live (DNS + SSL, per `STATE.md` "Domain live" 2026-07-20) — what's still missing is an actual mail provider/mailbox on it, which is the real remaining blocker, not the domain purchase. LLM-drafted replies (vs. the raw-KB-excerpt fallback) are deferred for now — no rush on the API key.

Stage 1 is demo-ready today when, running entirely offline against fixtures:

1. **Knowledge base search** — `office-agent kb search "<query>"` returns ranked, relevant excerpts from `samples/docs/` (real HELLFIRE/TETA+PI content: business model, module catalog, TETA+PI relationship) with source attribution. ✅ done, tested.
2. **Email triage** — `office-agent triage run` classifies a fixture inbox (`samples/inbox/sample_inbox.json`) into `sales_lead` / `routine_question` / `support_escalation` / `billing` / `spam` / `unclassified`, and routes everything except `routine_question` to a human with no draft generated. ✅ done, tested.
3. **Grounded draft replies** — routine questions get a draft reply built from knowledge-base excerpts (template-based today, LLM-based once `ANTHROPIC_API_KEY` is set — no code change needed to switch). Every draft is explicitly marked for human review; nothing is ever auto-sent. ✅ done, tested.
4. **Document generation** — `office-agent docgen offer` / `docgen contract` render a client offer or a module/people contract as Markdown, using the same field names as `internal-db`'s `crm.clients`/`crm.contracts` schema, with validation matching the DB's shape constraints. ✅ done, tested.
5. **Test suite** — 21 tests covering kb ranking, all six triage categories, draft grounding, IMAP message parsing (against a fake connection), and docgen validation/rendering, all passing offline. ✅ done.

## What's blocked, and on what

- **Real inbox (live IMAP)** — `IMAPSource` (`office_agent/email_triage/sources.py`) is code-complete and unit-tested against a fake IMAP connection, but not yet run against a real mailbox. Blocked on: a mail provider + mailbox on `hellfiresol.com` (the domain itself is already live — see `STATE.md` "Domain live"), per Bob's explicit sequencing — not a coding gap. Once the mailbox exists, this needs only `OFFICE_AGENT_IMAP_HOST/USER/PASSWORD` in `.env` (e.g. a Gmail/Workspace app password) and `office-agent triage run --source imap`.
- **LLM-drafted replies** — `email_triage/drafting.py` is code-complete and works with any `LLMClient`; deferred by Bob's choice, not blocked. Needs `ANTHROPIC_API_KEY` in `.env` and `office-agent triage run --use-llm` to switch on.

## Compliance cross-check (per session 11's coordination note, `STATE.md` row 06)

`compliance-layer/docs/legitimate-interest.md` flags that office-agent would need the same code-enforced `LegitimateInterestRecord` gate gtm-agent uses *if* its reply-drafting ever initiates contact with someone who hasn't written in first. As built, `email_triage/drafting.draft_reply()` only ever runs against an inbound `Email` already in the triage pipeline (see `pipeline.run_triage` — there is no path that drafts a message to someone who hasn't emailed first) — so per that same doc's own carve-out ("replying to an inbound email is not itself a Art. 6(1)(f) question"), Stage 1 as built does not need the gate. Revisit only if a future feature drafts outbound-initiated contact (not in scope for Stage 1 or Stage 2 as currently defined).

## What "demo to Bob" looks like concretely, today

Run `office-agent kb search "..."` against real HELLFIRE docs, `office-agent triage run` against the fixture inbox to show all six routing outcomes (including the sales lead correctly *not* getting an auto-draft), and `office-agent docgen offer --data samples/offer_example.json` to produce a ready-to-review offer document — all without any credentials, in under a minute.

## Next trigger for this session to resume

Once the domain/mailbox exists (session 02/03 territory) and Bob hands over IMAP credentials, come back to this module to run `IMAPSource` against real mail and report the result as a follow-up to this Stage 1 report, before starting Stage 2 (generic Gmail/Outlook client template).
