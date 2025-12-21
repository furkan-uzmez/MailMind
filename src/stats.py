"""
Usage statistics tracking for MailMind.
Logs app usage count and emails processed.
"""

import json
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich import box

console = Console()

# Stats file location (in project root)
STATS_FILE = Path(__file__).parent.parent / "logs/mailmind_stats.json"


@dataclass
class UsageStats:
    """Usage statistics container."""
    total_sessions: int = 0
    total_emails_processed: int = 0
    last_session_date: Optional[str] = None
    last_session_emails: int = 0
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "UsageStats":
        return cls(**data)


def load_stats() -> UsageStats:
    """Load stats from JSON file."""
    if STATS_FILE.exists():
        try:
            with open(STATS_FILE, "r") as f:
                data = json.load(f)
            return UsageStats.from_dict(data)
        except (json.JSONDecodeError, KeyError):
            pass
    return UsageStats()


def save_stats(stats: UsageStats):
    """Save stats to JSON file."""
    with open(STATS_FILE, "w") as f:
        json.dump(stats.to_dict(), f, indent=2)


def start_session() -> UsageStats:
    """Called when app starts. Increments session count."""
    stats = load_stats()
    stats.total_sessions += 1
    stats.last_session_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    stats.last_session_emails = 0
    save_stats(stats)
    return stats


def log_email_processed(stats: UsageStats) -> UsageStats:
    """Called when an email is processed. Increments email count."""
    stats.total_emails_processed += 1
    stats.last_session_emails += 1
    save_stats(stats)
    return stats


def show_stats():
    """Display usage statistics."""
    stats = load_stats()
    
    table = Table(title="📊 MailMind Usage Statistics", box=box.ROUNDED)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Total Sessions", str(stats.total_sessions))
    table.add_row("Total Emails Processed", str(stats.total_emails_processed))
    table.add_row("Last Session", stats.last_session_date or "Never")
    table.add_row("Emails in Last Session", str(stats.last_session_emails))
    
    console.print(table)


# Quick test
if __name__ == "__main__":
    show_stats()
