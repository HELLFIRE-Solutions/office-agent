# office-agent

A Python command-line tool for three office tasks: sorting incoming email into categories and drafting replies to routine questions, searching a folder of Markdown documents, and rendering offers and contracts from structured data. It works offline by default. A language model is used only when you ask it to draft a reply.

## Status

Prototype: version `0.1.0`, four commits, last change July 2026. Tests exist but no CI runs them. Email can come from a JSON file or from an IMAP mailbox. There is no OAuth connector for Gmail or Microsoft 365, no web interface, and nothing is ever sent: drafts are printed for a person to review.

## How it works

```
office_agent/
├── email_triage/    classify → (optionally) draft a reply
├── knowledge_base/  Markdown ingest + BM25 search
├── docgen/          Jinja2 templates for offers and contracts
├── llm.py           optional Anthropic client, imported lazily
└── cli.py           `office-agent` entry point
```

- **Triage** (`email_triage/classifier.py`): ordered regular-expression rules over subject and body. The first match wins. Categories: spam, sales lead, billing, support escalation, routine question, unclassified. Only *routine question* gets an automatic draft; the other categories are flagged for a human.
- **Drafting** (`email_triage/drafting.py`): retrieves the top three knowledge-base passages for the email. Without `--use-llm` it returns a template containing those passages. With `--use-llm` it asks Claude for a reply grounded in them.
- **Sources** (`email_triage/sources.py`): `JSONFileSource` reads a list of messages; `IMAPSource` reads up to 20 unseen messages over IMAP with SSL.
- **Knowledge base** (`knowledge_base/`): splits Markdown files by heading and paragraph, then ranks the chunks with a self-contained BM25 implementation. No vector database and no network.
- **Document generation** (`docgen/`): Jinja2 with `StrictUndefined`, so a missing required field raises an error instead of rendering blank. Templates: `offer`, `contract_module` (fixed-price), `contract_people` (monthly rate; tier `min`, `medium` or `fulltime`).

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

office-agent kb search "data residency"
office-agent triage run                       # uses samples/inbox/sample_inbox.json
office-agent docgen offer --data samples/offer_example.json
```

To draft replies with a model, install the extra with `pip install -e ".[llm]"`, set `ANTHROPIC_API_KEY`, then run `office-agent triage run --use-llm`.

## Configuration

Environment variables (see `.env.example`); none are needed for the default commands.

| Variable | Used by |
|---|---|
| `ANTHROPIC_API_KEY` | `triage run --use-llm` |
| `OFFICE_AGENT_IMAP_HOST`, `OFFICE_AGENT_IMAP_USER`, `OFFICE_AGENT_IMAP_PASSWORD` | `triage run --source imap` |

The model name is the `DEFAULT_MODEL` constant in `office_agent/llm.py`.

## Tests

```bash
pytest
```

21 tests in `tests/` cover the classifier and pipeline, the IMAP source (against a fake connection), BM25 search and both template types. None of them needs network access or an API key.

## Licence

MIT. See `LICENSE`.
