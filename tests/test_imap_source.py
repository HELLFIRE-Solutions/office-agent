import email.message

import pytest

from office_agent.email_triage.sources import IMAPSource


class FakeIMAPConnection:
    """Minimal stand-in for imaplib.IMAP4_SSL used to test parsing without a real server."""

    def __init__(self, host):
        self.host = host
        self.logged_in = False
        self.selected = None

        msg = email.message.EmailMessage()
        msg["From"] = "Prospect <prospect@example.com>"
        msg["Subject"] = "How do I use the knowledge base?"
        msg.set_content("Quick question about the docs search feature.")
        self._raw_messages = {b"1": msg.as_bytes()}

    def login(self, user, password):
        self.logged_in = True

    def select(self, mailbox):
        self.selected = mailbox

    def search(self, charset, criteria):
        return "OK", [b" ".join(self._raw_messages.keys())]

    def fetch(self, msg_id, parts):
        return "OK", [(b"1 (RFC822 {123}", self._raw_messages[msg_id])]

    def close(self):
        pass

    def logout(self):
        pass


def test_imap_source_requires_credentials():
    source = IMAPSource(host=None, user=None, password=None)
    with pytest.raises(RuntimeError, match="not all set"):
        source.fetch()


def test_imap_source_parses_messages_via_fake_connection():
    source = IMAPSource(
        host="imap.example.com",
        user="bob@hellfire.example",
        password="app-password",
        connection_factory=FakeIMAPConnection,
    )
    emails = source.fetch()

    assert len(emails) == 1
    assert emails[0].id == "1"
    assert "prospect@example.com" in emails[0].sender
    assert emails[0].subject == "How do I use the knowledge base?"
    assert "docs search" in emails[0].body
