"""Pluggable inbox sources.

JSONFileSource: fixture inbox, used for offline dogfood testing and the
test suite.

IMAPSource: real IMAP4_SSL connector for HELLFIRE's own mailbox (Stage 1
dogfooding — one hardcoded inbox, not yet configurable per client). A
generic Gmail/Outlook OAuth connector that a client can point at their own
tenant is Stage 2 scope; this is intentionally simpler because Stage 1
only ever needs to read Bob's own inbox. Needs OFFICE_AGENT_IMAP_HOST/
USER/PASSWORD in the environment to actually connect — code-complete but
blocked on Bob provisioning an app password (see README "Stage 1 setup").
"""

from __future__ import annotations

import email as email_lib
import imaplib
import os
from email.header import decode_header
from pathlib import Path
from typing import Protocol

from office_agent.email_triage.models import Email


class EmailSource(Protocol):
    def fetch(self) -> list[Email]: ...


class JSONFileSource:
    """Reads a JSON array of {id, sender, subject, body} objects."""

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def fetch(self) -> list[Email]:
        import json

        data = json.loads(self.path.read_text(encoding="utf-8"))
        return [Email(id=e["id"], sender=e["sender"], subject=e["subject"], body=e["body"]) for e in data]


def _decode(raw: str | None) -> str:
    if not raw:
        return ""
    parts = decode_header(raw)
    decoded = []
    for text, charset in parts:
        if isinstance(text, bytes):
            decoded.append(text.decode(charset or "utf-8", errors="ignore"))
        else:
            decoded.append(text)
    return "".join(decoded)


def _extract_body(msg: email_lib.message.Message) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain" and "attachment" not in str(
                part.get("Content-Disposition", "")
            ):
                payload = part.get_payload(decode=True)
                if payload:
                    return payload.decode(part.get_content_charset() or "utf-8", errors="ignore")
        return ""
    payload = msg.get_payload(decode=True)
    if not payload:
        return ""
    return payload.decode(msg.get_content_charset() or "utf-8", errors="ignore")


class IMAPSource:
    """Fetches unseen messages from a single IMAP mailbox (Stage 1: HELLFIRE's own inbox).

    `connection_factory` is injectable for testing — pass anything with the
    imaplib.IMAP4_SSL interface (login/select/search/fetch/close/logout).
    """

    def __init__(
        self,
        host: str | None = None,
        user: str | None = None,
        password: str | None = None,
        mailbox: str = "INBOX",
        limit: int = 20,
        connection_factory=imaplib.IMAP4_SSL,
    ):
        self.host = host or os.environ.get("OFFICE_AGENT_IMAP_HOST")
        self.user = user or os.environ.get("OFFICE_AGENT_IMAP_USER")
        self.password = password or os.environ.get("OFFICE_AGENT_IMAP_PASSWORD")
        self.mailbox = mailbox
        self.limit = limit
        self._connection_factory = connection_factory

    def fetch(self) -> list[Email]:
        if not (self.host and self.user and self.password):
            raise RuntimeError(
                "OFFICE_AGENT_IMAP_HOST/USER/PASSWORD are not all set. Use JSONFileSource for "
                "offline dogfooding, or provide credentials to connect to a real inbox."
            )

        conn = self._connection_factory(self.host)
        try:
            conn.login(self.user, self.password)
            conn.select(self.mailbox)
            status, data = conn.search(None, "UNSEEN")
            if status != "OK":
                raise RuntimeError(f"IMAP search failed: {status}")

            ids = data[0].split()[-self.limit :]
            emails: list[Email] = []
            for msg_id in ids:
                status, msg_data = conn.fetch(msg_id, "(RFC822)")
                if status != "OK" or not msg_data or not msg_data[0]:
                    continue
                raw = msg_data[0][1]
                msg = email_lib.message_from_bytes(raw)
                emails.append(
                    Email(
                        id=msg_id.decode(),
                        sender=_decode(msg.get("From")),
                        subject=_decode(msg.get("Subject")),
                        body=_extract_body(msg),
                    )
                )
            return emails
        finally:
            try:
                conn.close()
            except Exception:
                pass
            conn.logout()
