"""
Test suite for LLM classification and summarization.
Uses dummy emails fixture to test without hitting real mail server.
"""

import json
from pathlib import Path

import pytest
from rich.console import Console

console = Console()


# Load test fixture
FIXTURE_PATH = Path(__file__).parent / "dummy_emails.json"


@pytest.fixture
def dummy_emails():
    """Load dummy emails from fixture file."""
    with open(FIXTURE_PATH) as f:
        return json.load(f)


@pytest.fixture
def llm_engine():
    """Create LLM engine instance."""
    from src.core.llm_engine import LLMEngine
    return LLMEngine()


class TestLLMClassification:
    """Test email classification."""
    
    def test_classify_important_email(self, llm_engine, dummy_emails):
        """Important emails should be classified as IMPORTANT."""
        # Q4 Budget Meeting email
        email = dummy_emails[0]
        result = llm_engine.classify(
            subject=email["subject"],
            body=email["body"],
            sender=email["sender"]
        )
        
        console.print(f"[dim]Classification: {result}[/dim]")
        
        # Work emails from boss should be IMPORTANT
        from src.core.llm_engine import EmailCategory
        assert result.category == EmailCategory.IMPORTANT
    
    def test_classify_newsletter(self, llm_engine, dummy_emails):
        """Newsletter emails should be classified as NEWSLETTER."""
        # Dev Community digest
        email = dummy_emails[2]
        result = llm_engine.classify(
            subject=email["subject"],
            body=email["body"],
            sender=email["sender"]
        )
        
        console.print(f"[dim]Classification: {result}[/dim]")
        
        from src.core.llm_engine import EmailCategory
        assert result.category == EmailCategory.NEWSLETTER
    
    def test_classify_spam(self, llm_engine, dummy_emails):
        """Phishing/spam emails should be classified as SPAM."""
        # Fake bank security alert
        email = dummy_emails[3]
        result = llm_engine.classify(
            subject=email["subject"],
            body=email["body"],
            sender=email["sender"]
        )
        
        console.print(f"[dim]Classification: {result}[/dim]")
        
        from src.core.llm_engine import EmailCategory
        assert result.category == EmailCategory.SPAM


class TestLLMSummarization:
    """Test email summarization."""
    
    def test_summarize_meeting_email(self, llm_engine, dummy_emails):
        """Meeting emails should be summarized with key details."""
        email = dummy_emails[0]
        summary = llm_engine.summarize(
            subject=email["subject"],
            body=email["body"]
        )
        
        console.print(f"[dim]Summary: {summary}[/dim]")
        
        # Summary should exist and be concise
        assert summary
        assert len(summary) < 500  # Should be brief
        
        # Should mention key details
        summary_lower = summary.lower()
        assert any(word in summary_lower for word in ["meeting", "budget", "tomorrow", "q4"])
    
    def test_summarize_promo_email(self, llm_engine, dummy_emails):
        """Promotional emails should be summarized appropriately."""
        email = dummy_emails[1]
        summary = llm_engine.summarize(
            subject=email["subject"],
            body=email["body"]
        )
        
        console.print(f"[dim]Summary: {summary}[/dim]")
        
        assert summary
        assert len(summary) < 500


class TestLLMAvailability:
    """Test LLM availability checks."""
    
    def test_ollama_available(self, llm_engine):
        """Ollama should be running for tests."""
        is_available = llm_engine.is_available()
        
        if not is_available:
            pytest.skip("Ollama not running - start with: ollama serve")
        
        assert is_available


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
