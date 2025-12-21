"""
LLM Engine using Ollama for local inference.
Handles email classification, summarization, and reply drafting.
"""

import json
import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional

import ollama
from rich.console import Console
from rich.json import JSON
from rich.panel import Panel

from src.config import config

console = Console()


class EmailCategory(str, Enum):
    """Email classification categories."""
    IMPORTANT = "IMPORTANT"
    NEWSLETTER = "NEWSLETTER"
    SPAM = "SPAM"


@dataclass
class ClassificationResult:
    """Result of email classification."""
    category: EmailCategory
    reason: str
    confidence: float = 0.0
    
    @property
    def emoji(self) -> str:
        return {
            EmailCategory.IMPORTANT: "🔴",
            EmailCategory.NEWSLETTER: "🟡",
            EmailCategory.SPAM: "⚫"
        }.get(self.category, "❓")
    
    def __str__(self) -> str:
        return f"{self.emoji} {self.category.value}: {self.reason}"


class LLMEngine:
    """Ollama-based LLM engine for email processing."""
    
    # System prompts for different tasks
    CLASSIFIER_PROMPT = """You are an email classifier. Analyze the email and classify it into exactly ONE category.

Categories:
- IMPORTANT: Personal messages, work emails, urgent matters, action required
- NEWSLETTER: Marketing emails, subscriptions, promotional content, updates
- SPAM: Junk, scams, phishing attempts, unwanted solicitations

Return ONLY valid JSON in this exact format, no other text:
{"category": "IMPORTANT|NEWSLETTER|SPAM", "reason": "brief one-sentence explanation"}"""

    SUMMARIZER_PROMPT = """You are an email summarizer. Create a concise 1-2 sentence summary of the email.
Focus on: who sent it, what they want/need, any deadlines or action items.
Be brief and direct. Return ONLY the summary text, no formatting."""

    REPLY_PROMPT = """You are an email assistant helping draft a reply.
Write a professional, friendly reply based on the user's intent.
Keep it concise. Match the tone of the original email.
Return ONLY the reply text, ready to be sent."""

    QA_PROMPT = """You are an email assistant. Answer the user's question about their inbox.
Be helpful and concise. If you don't have enough information, say so.
Base your answer only on the provided email context."""

    def __init__(self, model: Optional[str] = None):
        self._model = model or config.ollama.model
        self._host = config.ollama.host
        
    def _call(self, system: str, user: str, temperature: float = 0.3) -> str:
        """Make a call to Ollama API."""
        try:
            response = ollama.chat(
                model=self._model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user}
                ],
                options={"temperature": temperature}
            )
            return response["message"]["content"].strip()
        except ollama.ResponseError as e:
            console.print(f"[red]❌ Ollama error: {e}[/red]")
            return ""
        except Exception as e:
            console.print(f"[red]❌ LLM call failed: {e}[/red]")
            console.print("[yellow]💡 Is Ollama running? Try: ollama serve[/yellow]")
            return ""

    def _extract_json(self, text: str) -> dict:
        """Extract JSON from LLM response, handling markdown code blocks."""
        # Try to find JSON in code blocks
        code_block = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
        if code_block:
            text = code_block.group(1)
        
        # Try to find JSON object
        json_match = re.search(r'\{[^{}]*\}', text)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        # Try parsing the whole thing
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {}

    def classify(self, subject: str, body: str, sender: str = "") -> ClassificationResult:
        """
        Classify an email into IMPORTANT, NEWSLETTER, or SPAM.
        
        Returns:
            ClassificationResult with category and reasoning
        """
        email_text = f"""From: {sender}
Subject: {subject}

{body[:1500]}"""  # Limit body to save tokens

        console.print("[cyan]🤖 Classifying email...[/cyan]")
        
        response = self._call(self.CLASSIFIER_PROMPT, email_text)
        
        if not response:
            return ClassificationResult(
                category=EmailCategory.NEWSLETTER,
                reason="Classification failed - defaulting to NEWSLETTER"
            )
        
        data = self._extract_json(response)
        
        try:
            category = EmailCategory(data.get("category", "NEWSLETTER").upper())
        except ValueError:
            category = EmailCategory.NEWSLETTER
        
        reason = data.get("reason", "No reason provided")
        
        result = ClassificationResult(category=category, reason=reason)
        
        # Pretty print the result
        console.print(Panel(
            f"[bold]{result.emoji} {category.value}[/bold]\n[dim]{reason}[/dim]",
            title="Classification",
            border_style="cyan"
        ))
        
        return result
    
    def summarize(self, subject: str, body: str) -> str:
        """
        Summarize an email into 1-2 sentences.
        
        Returns:
            Concise summary string
        """
        email_text = f"""Subject: {subject}

{body[:1500]}"""

        console.print("[cyan]🤖 Summarizing...[/cyan]")
        
        summary = self._call(self.SUMMARIZER_PROMPT, email_text)
        
        if not summary:
            return f"Email about: {subject}"
        
        console.print(Panel(summary, title="Summary", border_style="green"))
        
        return summary
    
    def draft_reply(self, original_email: str, user_intent: str) -> str:
        """
        Draft a reply based on user's intent.
        
        Args:
            original_email: The email being replied to
            user_intent: What the user wants to say (e.g., "accept the meeting")
            
        Returns:
            Draft reply text
        """
        prompt = f"""Original Email:
{original_email[:1000]}

User wants to: {user_intent}

Draft a reply:"""

        console.print("[cyan]🤖 Drafting reply...[/cyan]")
        
        reply = self._call(self.REPLY_PROMPT, prompt, temperature=0.5)
        
        if reply:
            console.print(Panel(reply, title="Draft Reply", border_style="blue"))
        
        return reply
    
    def ask(self, question: str, email_context: str) -> str:
        """
        Answer a question about emails.
        
        Args:
            question: User's question
            email_context: Relevant email content
            
        Returns:
            Answer string
        """
        prompt = f"""Email Context:
{email_context[:2000]}

Question: {question}"""

        console.print("[cyan]🤖 Thinking...[/cyan]")
        
        answer = self._call(self.QA_PROMPT, prompt, temperature=0.4)
        
        if answer:
            console.print(Panel(answer, title="Answer", border_style="magenta"))
        
        return answer
    
    def is_available(self) -> bool:
        """Check if Ollama is running and model is available."""
        try:
            models = ollama.list()
            available = [m["name"].split(":")[0] for m in models.get("models", [])]
            
            if self._model.split(":")[0] in available:
                console.print(f"[green]✅ Ollama ready with model: {self._model}[/green]")
                return True
            else:
                console.print(f"[yellow]⚠️  Model {self._model} not found. Available: {available}[/yellow]")
                console.print(f"[yellow]💡 Run: ollama pull {self._model}[/yellow]")
                return False
                
        except Exception as e:
            console.print(f"[red]❌ Ollama not available: {e}[/red]")
            console.print("[yellow]💡 Start Ollama with: ollama serve[/yellow]")
            return False


# Quick test
if __name__ == "__main__":
    engine = LLMEngine()
    
    if engine.is_available():
        # Test classification
        result = engine.classify(
            subject="Q4 Budget Review Meeting Tomorrow",
            body="Hi team, reminder that we have the Q4 budget review meeting tomorrow at 2pm. Please bring your department reports.",
            sender="boss@company.com"
        )
        
        # Test summarization
        summary = engine.summarize(
            subject="Q4 Budget Review Meeting Tomorrow",
            body="Hi team, reminder that we have the Q4 budget review meeting tomorrow at 2pm. Please bring your department reports."
        )
