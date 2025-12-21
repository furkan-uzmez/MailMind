"""
Email client for IMAP connection and email parsing.
Securely fetches unread emails and extracts content.
"""

import email
import imaplib
import re
from dataclasses import dataclass
from email.header import decode_header
from email.message import Message
from typing import Generator, Optional

from bs4 import BeautifulSoup
from rich.console import Console

from src.config import config

console = Console()


@dataclass
class Email:
    """Parsed email representation."""
    uid: str
    subject: str
    sender: str
    sender_name: str
    body: str
    is_html: bool = False
    
    def __str__(self) -> str:
        return f"📧 From: {self.sender_name} <{self.sender}>\n   Subject: {self.subject}"


class EmailClient:
    """IMAP email client with secure connection."""
    
    def __init__(self):
        self._config = config.email
        self._connection: Optional[imaplib.IMAP4_SSL] = None
    
    def __enter__(self) -> "EmailClient":
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.disconnect()
    
    def connect(self) -> bool:
        """Establish secure IMAP connection."""
        if not self._config.validate():
            return False
        
        try:
            console.print(f"[cyan]🔌 Connecting to {self._config.imap_server}...[/cyan]")
            self._connection = imaplib.IMAP4_SSL(
                self._config.imap_server,
                self._config.imap_port
            )
            self._connection.login(self._config.user, self._config.password)
            console.print("[green]✅ Connected successfully![/green]")
            return True
        except imaplib.IMAP4.error as e:
            console.print(f"[red]❌ IMAP login failed: {e}[/red]")
            return False
        except Exception as e:
            console.print(f"[red]❌ Connection error: {e}[/red]")
            return False
    
    def disconnect(self) -> None:
        """Close IMAP connection gracefully."""
        if self._connection:
            try:
                self._connection.logout()
                console.print("[dim]🔌 Disconnected from mail server.[/dim]")
            except Exception:
                pass
            self._connection = None
    
    def fetch_unread(self, folder: str = "INBOX", limit: int = 10) -> Generator[Email, None, None]:
        """
        Fetch unread emails from the specified folder.
        
        Args:
            folder: Mailbox folder to check (default: INBOX)
            limit: Maximum number of emails to fetch
            
        Yields:
            Email objects with parsed content
        """
        if not self._connection:
            console.print("[red]❌ Not connected. Call connect() first.[/red]")
            return
        
        try:
            self._connection.select(folder)
            status, messages = self._connection.search(None, "UNSEEN")
            
            if status != "OK":
                console.print("[yellow]⚠️  Could not search for unread emails.[/yellow]")
                return
            
            message_ids = messages[0].split()
            total = len(message_ids)
            
            if total == 0:
                console.print("[dim]📭 No unread emails.[/dim]")
                return
            
            console.print(f"[cyan]📬 Found {total} unread email(s)[/cyan]")
            
            # Fetch most recent emails first (reverse order), apply limit
            for msg_id in reversed(message_ids[-limit:]):
                try:
                    email_obj = self._fetch_single(msg_id)
                    if email_obj:
                        yield email_obj
                except Exception as e:
                    console.print(f"[yellow]⚠️  Error parsing email {msg_id}: {e}[/yellow]")
                    continue
                    
        except imaplib.IMAP4.error as e:
            console.print(f"[red]❌ IMAP error: {e}[/red]")
    
    def _fetch_single(self, msg_id: bytes) -> Optional[Email]:
        """Fetch and parse a single email by ID."""
        status, msg_data = self._connection.fetch(msg_id, "(RFC822)")
        
        if status != "OK" or not msg_data[0]:
            return None
        
        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)
        
        return self._parse_email(msg_id.decode(), msg)
    
    def _parse_email(self, uid: str, msg: Message) -> Email:
        """Parse email message into Email dataclass."""
        # Decode subject
        subject = self._decode_header(msg["Subject"]) or "(No Subject)"
        
        # Parse sender
        sender_raw = msg["From"] or ""
        sender_name, sender_email = self._parse_sender(sender_raw)
        
        # Extract body
        body, is_html = self._extract_body(msg)
        
        return Email(
            uid=uid,
            subject=subject,
            sender=sender_email,
            sender_name=sender_name,
            body=body,
            is_html=is_html
        )
    
    def _decode_header(self, header: Optional[str]) -> str:
        """Decode email header (handles encoding like UTF-8, ISO-8859-1)."""
        if not header:
            return ""
        
        decoded_parts = []
        for part, encoding in decode_header(header):
            if isinstance(part, bytes):
                decoded_parts.append(part.decode(encoding or "utf-8", errors="replace"))
            else:
                decoded_parts.append(part)
        
        return " ".join(decoded_parts)
    
    def _parse_sender(self, sender: str) -> tuple[str, str]:
        """Extract name and email from sender string."""
        # Pattern: "Name" <email@domain.com> or Name <email@domain.com>
        match = re.match(r'^"?([^"<]*)"?\s*<?([^>]+)>?$', sender.strip())
        
        if match:
            name = match.group(1).strip() or match.group(2).split("@")[0]
            email_addr = match.group(2).strip()
            return name, email_addr
        
        return sender, sender
    
    def _extract_body(self, msg: Message) -> tuple[str, bool]:
        """Extract email body, preferring plain text over HTML."""
        body = ""
        is_html = False
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))
                
                # Skip attachments
                if "attachment" in content_disposition:
                    continue
                
                if content_type == "text/plain":
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or "utf-8"
                        body = payload.decode(charset, errors="replace")
                        break  # Prefer plain text
                        
                elif content_type == "text/html" and not body:
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or "utf-8"
                        html_body = payload.decode(charset, errors="replace")
                        body = self._strip_html(html_body)
                        is_html = True
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or "utf-8"
                content = payload.decode(charset, errors="replace")
                
                if msg.get_content_type() == "text/html":
                    body = self._strip_html(content)
                    is_html = True
                else:
                    body = content
        
        # Clean up body
        body = self._clean_body(body)
        return body, is_html
    
    def _strip_html(self, html: str) -> str:
        """Strip HTML tags and extract readable text using BeautifulSoup."""
        soup = BeautifulSoup(html, "lxml")
        
        # Remove script and style elements
        for element in soup(["script", "style", "head", "meta"]):
            element.decompose()
        
        # Get text
        text = soup.get_text(separator="\n")
        return text
    
    def _clean_body(self, body: str) -> str:
        """Clean up email body text."""
        # Remove excessive whitespace
        lines = [line.strip() for line in body.splitlines()]
        lines = [line for line in lines if line]  # Remove empty lines
        
        # Collapse multiple newlines
        text = "\n".join(lines)
        
        # Limit length to save LLM tokens
        max_chars = 2000
        if len(text) > max_chars:
            text = text[:max_chars] + "\n... [truncated]"
        
        return text
    
    def mark_as_read(self, uid: str) -> bool:
        """Mark an email as read."""
        if not self._connection:
            return False
        
        try:
            self._connection.store(uid.encode(), "+FLAGS", "\\Seen")
            return True
        except Exception:
            return False


# Quick test
if __name__ == "__main__":
    with EmailClient() as client:
        for mail in client.fetch_unread(limit=5):
            console.print(f"\n{mail}")
            console.print(f"[dim]Body preview: {mail.body[:200]}...[/dim]")
