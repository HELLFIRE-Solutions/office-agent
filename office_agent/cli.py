from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from office_agent.docgen.generate import DocgenError, render_contract, render_offer
from office_agent.email_triage.pipeline import run_triage
from office_agent.email_triage.sources import IMAPSource, JSONFileSource
from office_agent.knowledge_base.index import BM25Index
from office_agent.knowledge_base.ingest import ingest_directory
from office_agent.llm import AnthropicClient


def _build_index(docs_dir: str) -> BM25Index:
    raw_chunks = ingest_directory(docs_dir)
    return BM25Index.from_raw_chunks(raw_chunks)


def cmd_kb_search(args: argparse.Namespace) -> int:
    index = _build_index(args.docs_dir)
    results = index.search(args.query, top_k=args.top_k)
    if not results:
        print("No matches.")
        return 0
    for r in results:
        heading = f" — {r.chunk.heading}" if r.chunk.heading else ""
        print(f"[{r.score:.3f}] {r.chunk.source}{heading}")
        print(f"    {r.chunk.text[:200].replace(chr(10), ' ')}")
    return 0


def cmd_triage_run(args: argparse.Namespace) -> int:
    source = IMAPSource() if args.source == "imap" else JSONFileSource(args.inbox)
    index = _build_index(args.docs_dir) if args.docs_dir else None
    llm = AnthropicClient() if args.use_llm else None

    results = run_triage(source, kb_index=index, llm=llm)
    for r in results:
        print(f"--- email {r.email.id} ({r.email.sender}) ---")
        print(f"subject: {r.email.subject}")
        print(f"category: {r.category.value}  requires_human: {r.requires_human}  rule: {r.matched_rule}")
        if r.draft_reply:
            print("draft reply:")
            print(r.draft_reply)
        print()
    return 0


def cmd_docgen_offer(args: argparse.Namespace) -> int:
    data = json.loads(Path(args.data).read_text(encoding="utf-8"))
    try:
        rendered = render_offer(data)
    except DocgenError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    _write_output(rendered, args.out)
    return 0


def cmd_docgen_contract(args: argparse.Namespace) -> int:
    data = json.loads(Path(args.data).read_text(encoding="utf-8"))
    try:
        rendered = render_contract(data)
    except DocgenError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    _write_output(rendered, args.out)
    return 0


def _write_output(text: str, out: str | None) -> None:
    if out:
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        Path(out).write_text(text, encoding="utf-8")
        print(f"wrote {out}")
    else:
        print(text)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="office-agent")
    subparsers = parser.add_subparsers(dest="command", required=True)

    kb = subparsers.add_parser("kb", help="knowledge base commands")
    kb_sub = kb.add_subparsers(dest="kb_command", required=True)
    kb_search = kb_sub.add_parser("search", help="search the knowledge base")
    kb_search.add_argument("query")
    kb_search.add_argument("--docs-dir", default="samples/docs")
    kb_search.add_argument("--top-k", type=int, default=5)
    kb_search.set_defaults(func=cmd_kb_search)

    triage = subparsers.add_parser("triage", help="email triage commands")
    triage_sub = triage.add_subparsers(dest="triage_command", required=True)
    triage_run = triage_sub.add_parser("run", help="triage an inbox")
    triage_run.add_argument("--source", choices=["json", "imap"], default="json")
    triage_run.add_argument("--inbox", default="samples/inbox/sample_inbox.json", help="used when --source json")
    triage_run.add_argument("--docs-dir", default="samples/docs")
    triage_run.add_argument("--use-llm", action="store_true", help="use ANTHROPIC_API_KEY to draft replies")
    triage_run.set_defaults(func=cmd_triage_run)

    docgen = subparsers.add_parser("docgen", help="document generation commands")
    docgen_sub = docgen.add_subparsers(dest="docgen_command", required=True)

    docgen_offer = docgen_sub.add_parser("offer", help="render a client offer")
    docgen_offer.add_argument("--data", required=True)
    docgen_offer.add_argument("--out")
    docgen_offer.set_defaults(func=cmd_docgen_offer)

    docgen_contract = docgen_sub.add_parser("contract", help="render a contract")
    docgen_contract.add_argument("--data", required=True)
    docgen_contract.add_argument("--out")
    docgen_contract.set_defaults(func=cmd_docgen_contract)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
