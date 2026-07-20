# HELLFIRE Module Catalog

Numbered by build order (lower number = built earlier), not necessarily by
sale price. Each module is a public GitHub repo under `HELLFIRE-Solutions`
(MIT licensed), except `internal-db` which is private because it holds
client data.

## 1. AI GTM / AI Sales (`gtm-agent`)

Warm-lead qualification (LinkedIn/referrals — explicitly not cold email,
which carries legal risk in DACH), personalized outreach, calendar
booking. Built first because it both sells and demos itself. Template =
configurable GTM-agent framework pluggable into a client's CRM/email/
LinkedIn.

## 2. AI Office (`office-agent`)

Email triage and draft replies to routine requests, internal knowledge
base search over HELLFIRE/TETA+PI documentation, and document automation
for contracts and client offers. This module. Stage 1 serves HELLFIRE's
own internal workflow; Stage 2 extracts a template that connects to a
client's Gmail/Outlook and their own internal knowledge repository.

## 3. RAG 01 (`rag-01`)

Infrastructure module underpinning AI Office and future sector agents.
RAG over HELLFIRE/TETA+PI's own docs (Data Room, pitch deck, specs).
Open questions as of the last status check: Qdrant vs pgvector, self-
hosted vs managed, EU hosting location.

## 4. UNI Tag / GEO-AEO (`uni-tag`)

llms.txt, schema.org structured data, agent-readable meta tags — applied
first to HELLFIRE's own site, then measured for AI-search visibility
across Perplexity, ChatGPT search, and Claude.

## 5. AI MCP Dev (`mcp-dev`)

Reuses TETA+PI's MCP server experience (resolve -> verify -> profile
chain) as a repeatable playbook / starter-kit for client CRM/API
integrations.

## 6. In-house LLM (`inhouse-llm`)

Self-hosted open-source model (Llama/Mistral class). Highest price point;
needs prior modules mature first.

## 7. Compliance / Trust layer (`compliance-layer`)

DSGVO/AI Act compliance audit framework, built on TWIRA (Trust-Weighted
Intent Routing) verification logic. Can be sold standalone or as a
required add-on to other modules.

## 8. Onboarding / Training (`onboarding`)

Standardized onboarding package (sessions + docs + video/guides) — itself
a paid catalog item, not just a process step bundled into a module sale.

## Cross-cutting infrastructure (not numbered modules)

- **Verification layer** — GitHub-based verification of contractors
  before pool admission; a public repo with relevant implementation work
  stands in for a resume or diploma.
- **Nostr time-tracker** — cryptographically signed work log tied to each
  contractor's Nostr keypair.
