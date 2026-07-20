# HELLFIRE AI Solutions — Office Agent

Модуль 2. Email-тріаж і драфти відповідей на рутинні запити, internal knowledge base (документація HELLFIRE + TETA+PI) з пошуком, автоматизація документообігу (контракти, оффери клієнтам).

**Dogfooding:** спочатку обслуговує внутрішні процеси HELLFIRE/TETA+PI (Етап 1). Потім витягується office-agent template, що підключається до Gmail/Outlook + внутрішнього knowledge repository клієнта (Етап 2).

## Технічні рішення (зафіксовано 2026-07-20, деталі: `docs/architecture.md`)

- **Knowledge base:** лексичний BM25-пошук (`office_agent/knowledge_base/`), без vector DB і без API-ключа — rag-01 (сесія 07) ще не має pipeline, тому дублювати нічого, і замінити backend можна пізніше без зміни інтерфейсу `search()`.
- **LLM:** Anthropic API (`office_agent/llm.py`), опційний і lazy-imported — kb-пошук і rule-based тріаж працюють без жодного ключа. Драфт-реплаї без LLM падають на шаблон із сирими excerpt'ами з KB, чітко позначений як `[DRAFT]`.
- **Email-тріаж:** deterministic keyword-класифікатор, 6 категорій. Драфт генерується лише для `routine_question` — усе інше (sales, billing, escalation, spam, unclassified) йде до людини без драфту. Ніщо не відправляється автоматично.
- **Inbox connector:** реальний IMAP-конектор (`IMAPSource`) на одну поштову скриньку HELLFIRE — не generic multi-tenant OAuth (це Етап 2). Домен `hellfiresol.com` вже live (DNS+SSL), але поштова скринька на ньому ще не піднята — деталі в `docs/demo-ready-criteria.md`.
- **Docgen:** Jinja2-шаблони (`office_agent/docgen/`), поля відповідають схемі `crm.clients`/`crm.contracts` з `internal-db`, щоб DB-рядок можна було передати напряму без translation layer.

## Швидкий старт

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env  # опційно: ANTHROPIC_API_KEY, OFFICE_AGENT_IMAP_*

office-agent kb search "EU data residency DSGVO"
office-agent triage run                              # fixture-інбокс, без креденшелів
office-agent triage run --source imap --use-llm       # реальна пошта + LLM-драфти (потребує .env)
office-agent docgen offer --data samples/offer_example.json --out out/offer.md
```

`pytest tests/` — 21 тест, покривають BM25-ранжування, усі 6 категорій тріажу, grounding драфтів, парсинг IMAP-повідомлень (фейкове з'єднання) і валідацію/рендер docgen.

## Статус

Етап 1 — код готовий і протестований офлайн (fixtures у `samples/`). Заблоковано не на код, а на Bob-а: реальний IMAP (домен `hellfiresol.com` вже live, чекає поштову скриньку на ньому) і `ANTHROPIC_API_KEY` (свідомо відкладено). Деталі й критерії demo-ready: `docs/demo-ready-criteria.md`.

**Ліцензія:** MIT.
