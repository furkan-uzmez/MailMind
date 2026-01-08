"""
Main event loop for LocalMail-Voice-Assistant.
Fetches emails, processes with LLM, and provides voice interface.
"""

import asyncio
import sys
from dataclasses import dataclass
from typing import Optional

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
from rich.text import Text
from rich import box

from src.config import config
from src.parameters import EMAIL_COUNT, BODY_PREVIEW_LENGTH
from src.stats import start_session, log_email_processed, show_stats, UsageStats
from src.core.email_client import EmailClient, Email
from src.core.llm import create_llm_engine, EmailCategory, ClassificationResult
from src.core.security import LinkScanner
from src.audio.tts import create_tts_engine
from src.audio.stt import create_stt_engine
from src.core.graph import MailWorkflow

console = Console()


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║                           CYBERPUNK BANNER                                 ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

BANNER = """
[bold cyan]
 ███╗   ███╗ █████╗ ██╗██╗     ███╗   ███╗██╗███╗   ██╗██████╗ 
 ████╗ ████║██╔══██╗██║██║     ████╗ ████║██║████╗  ██║██╔══██╗
 ██╔████╔██║███████║██║██║     ██╔████╔██║██║██╔██╗ ██║██║  ██║
 ██║╚██╔╝██║██╔══██║██║██║     ██║╚██╔╝██║██║██║╚██╗██║██║  ██║
 ██║ ╚═╝ ██║██║  ██║██║███████╗██║ ╚═╝ ██║██║██║ ╚████║██████╔╝
 ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝╚══════╝╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚═════╝ 
[/bold cyan]
[dim]🔒 Privacy-First Local AI Email Assistant • v0.2.0 (LangGraph)[/dim]
"""


@dataclass
class ProcessedEmail:
    """Email with classification and summary."""
    email: Email
    classification: ClassificationResult
    summary: str
    spoken: bool = False


class MailMindApp:
    """Main application orchestrating all components."""
    
    def __init__(self, voice_mode: bool = True):
        self._email_client = EmailClient()
        self._llm = create_llm_engine()  # Uses LLM_PROVIDER env var
        self._scanner = LinkScanner()
        self._speaker = create_tts_engine() if voice_mode else None  # Uses TTS_PROVIDER
        self._listener = create_stt_engine() if voice_mode else None  # Uses STT_PROVIDER
        self._voice_mode = voice_mode
        self._processed_emails: list[ProcessedEmail] = []
        self._running = False
        self._stats: UsageStats = None  # Will be initialized on run
        
        # Initialize Workflow
        self._workflow = MailWorkflow(
            llm_engine=self._llm,
            scanner=self._scanner,
            tts_engine=self._speaker,
            stt_engine=self._listener
        )
        
    def run(self, continuous: bool = False, check_interval: int = 60):
        """
        Main application loop.
        
        Args:
            continuous: If True, keep checking for new emails
            check_interval: Seconds between email checks (if continuous)
        """
        console.print(BANNER)
        self._show_status()
        
        # Start tracking session
        self._stats = start_session()
        console.print(f"[dim]📊 Session #{self._stats.total_sessions} | Total emails processed: {self._stats.total_emails_processed}[/dim]\n")
        
        if not self._preflight_check():
            return
        
        self._running = True
        
        try:
            if continuous:
                self._run_continuous(check_interval)
            else:
                self._run_once()
        except KeyboardInterrupt:
            console.print("\n[yellow]👋 Interrupted. Goodbye![/yellow]")
        finally:
            self._running = False
            # Show usage stats
            show_stats()
    
    def _show_status(self):
        """Display system status."""
        table = Table(title="System Status", box=box.ROUNDED)
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Provider", style="dim")
        
        # Email
        email_ok = bool(config.email.user and config.email.password)
        table.add_row(
            "Email",
            "✅ Configured" if email_ok else "❌ Not configured",
            config.email.imap_server if email_ok else "Set EMAIL_USER & EMAIL_PASS"
        )
        
        # LLM
        table.add_row(
            "LLM",
            "⏳ Checking...",
            self._llm.provider_name
        )
        
        # TTS
        if self._speaker:
            table.add_row("TTS", "✅ Enabled", self._speaker.provider_name)
        else:
            table.add_row("TTS", "❌ Disabled", "--no-voice")
        
        # STT
        if self._listener:
            table.add_row("STT", "✅ Enabled", self._listener.provider_name)
        else:
            table.add_row("STT", "❌ Disabled", "--no-voice")
        
        console.print(table)
        console.print()
    
    def _preflight_check(self) -> bool:
        """Verify all systems are ready."""
        console.print("[bold]🔍 Running preflight checks...[/bold]\n")
        
        # Check email config
        if not config.email.validate():
            return False
        
        # Check LLM
        if not self._llm.is_available():
            console.print("[red]❌ LLM not available. Exiting.[/red]")
            return False
        
        # Check TTS
        if self._speaker and not self._speaker.is_available():
            console.print("[yellow]⚠️  TTS not available, continuing without voice output[/yellow]")
            self._speaker = None
        
        # Check STT
        if self._listener:
            self._listener.test_microphone()
        
        console.print("\n[bold green]✅ All systems go![/bold green]\n")
        return True
    
    def _run_once(self):
        """Process emails once."""
        console.print(Panel("[bold]📬 Fetching emails...[/bold]", border_style="cyan"))
        
        with self._email_client as client:
            emails = list(client.fetch_unread(limit=EMAIL_COUNT))
            
            if not emails:
                console.print("[dim]No unread emails. You're all caught up! 🎉[/dim]")
                return
            
            # Process each email
            for i, email in enumerate(emails, 1):
                console.rule(f"[bold]Email {i}/{len(emails)}[/bold]")
                self._process_email(email)
        
        self._show_summary()
    
    def _run_continuous(self, interval: int):
        """Continuously check for new emails."""
        console.print(Panel(
            f"[bold]🔄 Continuous mode[/bold]\n"
            f"Checking every {interval} seconds. Press Ctrl+C to stop.",
            border_style="cyan"
        ))
        
        while self._running:
            self._run_once()
            
            if not self._running:
                break
            
            # Wait for next check
            console.print(f"\n[dim]⏰ Next check in {interval} seconds...[/dim]")
            try:
                for _ in range(interval):
                    if not self._running:
                        break
                    asyncio.run(asyncio.sleep(1))
            except KeyboardInterrupt:
                break
    
    def _process_email(self, email: Email):
        """Process a single email using LangGraph."""
        console.print(f"\n{email}\n")
        
        # Show email body preview
        body_preview = email.body[:BODY_PREVIEW_LENGTH] + "..." if len(email.body) > BODY_PREVIEW_LENGTH else email.body
        console.print(Panel(
            body_preview,
            title="[bold]📄 Email Content[/bold]",
            border_style="dim",
            padding=(0, 1)
        ))
        
        # Invoke the graph
        config = {"configurable": {"thread_id": email.uid}, "recursion_limit": 100}
        try:
            final_state = self._workflow.graph.invoke(
                {"email": email, "messages": []},
                config=config
            )
            
            processed = ProcessedEmail(
                email=email,
                classification=final_state.get("classification"),
                summary=final_state.get("summary", ""),
                spoken=True # Assuming graph spoke it
            )
            self._processed_emails.append(processed)
            
            # Log this email was processed
            if self._stats:
                self._stats = log_email_processed(self._stats)
                
        except Exception as e:
            console.print(f"[red]Error processing email: {e}[/red]")

    def _show_summary(self):
        """Show summary of processed emails."""
        if not self._processed_emails:
            return
        
        console.print("\n")
        console.rule("[bold]📊 Session Summary[/bold]")
        
        table = Table(box=box.SIMPLE)
        table.add_column("", width=3)
        table.add_column("From", style="cyan")
        table.add_column("Subject", style="white")
        table.add_column("Category")
        
        for p in self._processed_emails:
            if not p.classification:
                continue
                
            cat_style = {
                EmailCategory.IMPORTANT: "bold red",
                EmailCategory.NEWSLETTER: "yellow",
                EmailCategory.SPAM: "dim"
            }.get(p.classification.category, "white")
            
            table.add_row(
                p.classification.emoji,
                p.email.sender_name[:20],
                p.email.subject[:40],
                Text(p.classification.category.value, style=cat_style)
            )
        
        console.print(table)
        
        # Stats
        important = sum(1 for p in self._processed_emails if p.classification and p.classification.category == EmailCategory.IMPORTANT)
        newsletter = sum(1 for p in self._processed_emails if p.classification and p.classification.category == EmailCategory.NEWSLETTER)
        spam = sum(1 for p in self._processed_emails if p.classification and p.classification.category == EmailCategory.SPAM)
        
        console.print(f"\n🔴 Important: {important}  🟡 Newsletter: {newsletter}  ⚫ Spam: {spam}")


def main():
    """Entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="MailMind - Privacy-First Local AI Email Assistant"
    )
    parser.add_argument(
        "--no-voice", 
        action="store_true",
        help="Disable voice mode (no TTS/STT)"
    )
    parser.add_argument(
        "--continuous", "-c",
        action="store_true",
        help="Continuously check for new emails"
    )
    parser.add_argument(
        "--interval", "-i",
        type=int,
        default=60,
        help="Interval between checks in seconds (default: 60)"
    )
    
    args = parser.parse_args()
    
    app = MailMindApp(voice_mode=not args.no_voice)
    app.run(continuous=args.continuous, check_interval=args.interval)


if __name__ == "__main__":
    main()
