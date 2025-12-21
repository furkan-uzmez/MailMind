"""
OpenAI LLM provider for cloud-based inference.
Uses the OpenAI API (GPT-4, GPT-3.5-turbo, etc.).
"""

import json
import os
import re
from typing import Optional

from rich.console import Console
from rich.panel import Panel

from .base import BaseLLMEngine, ClassificationResult, EmailCategory

console = Console()


class OpenAIEngine(BaseLLMEngine):
    """OpenAI-based LLM engine for cloud inference."""
    
    def __init__(
        self, 
        model: Optional[str] = None, 
        api_key: Optional[str] = None
    ):
        self._model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self._api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self._client = None
        
    @property
    def provider_name(self) -> str:
        return "openai"
    
    def _get_client(self):
        """Lazy-load OpenAI client."""
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self._api_key)
            except ImportError:
                console.print("[red]❌ openai package not installed[/red]")
                console.print("[yellow]💡 Run: pip install openai[/yellow]")
                raise
        return self._client
    
    def _call(self, system: str, user: str, temperature: float = 0.3) -> str:
        """Make a call to OpenAI API."""
        try:
            client = self._get_client()
            
            response = client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user}
                ],
                temperature=temperature,
                max_tokens=500
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            console.print(f"[red]❌ OpenAI error: {e}[/red]")
            return ""

    def _extract_json(self, text: str) -> dict:
        """Extract JSON from LLM response."""
        code_block = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
        if code_block:
            text = code_block.group(1)
        
        json_match = re.search(r'\{[^{}]*\}', text)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {}

    def is_available(self) -> bool:
        """Check if OpenAI API is configured."""
        if not self._api_key:
            console.print("[yellow]⚠️  OPENAI_API_KEY not set in environment[/yellow]")
            return False
        
        try:
            # Test with a simple call
            client = self._get_client()
            client.models.list()
            console.print(f"[green]✅ OpenAI ready with model: {self._model}[/green]")
            return True
        except Exception as e:
            console.print(f"[red]❌ OpenAI not available: {e}[/red]")
            return False

    def classify(self, subject: str, body: str, sender: str = "") -> ClassificationResult:
        """Classify an email into IMPORTANT, NEWSLETTER, or SPAM."""
        email_text = f"""From: {sender}
Subject: {subject}

{body[:1500]}"""

        console.print("[cyan]🤖 Classifying email (OpenAI)...[/cyan]")
        
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
        
        console.print(Panel(
            f"[bold]{result.emoji} {category.value}[/bold]\n[dim]{reason}[/dim]",
            title="Classification (OpenAI)",
            border_style="cyan"
        ))
        
        return result
    
    def summarize(self, subject: str, body: str) -> str:
        """Summarize an email into 1-2 sentences."""
        email_text = f"""Subject: {subject}

{body[:1500]}"""

        console.print("[cyan]🤖 Summarizing (OpenAI)...[/cyan]")
        
        summary = self._call(self.SUMMARIZER_PROMPT, email_text)
        
        if not summary:
            return f"Email about: {subject}"
        
        console.print(Panel(summary, title="Summary", border_style="green"))
        
        return summary
    
    def draft_reply(self, original_email: str, user_intent: str) -> str:
        """Draft a reply based on user's intent."""
        prompt = f"""Original Email:
{original_email[:1000]}

User wants to: {user_intent}

Draft a reply:"""

        console.print("[cyan]🤖 Drafting reply (OpenAI)...[/cyan]")
        
        reply = self._call(self.REPLY_PROMPT, prompt, temperature=0.5)
        
        if reply:
            console.print(Panel(reply, title="Draft Reply", border_style="blue"))
        
        return reply
    
    def ask(self, question: str, email_context: str) -> str:
        """Answer a question about emails."""
        prompt = f"""Email Context:
{email_context[:2000]}

Question: {question}"""

        console.print("[cyan]🤖 Thinking (OpenAI)...[/cyan]")
        
        answer = self._call(self.QA_PROMPT, prompt, temperature=0.4)
        
        if answer:
            console.print(Panel(answer, title="Answer", border_style="magenta"))
        
        return answer


# Quick test
if __name__ == "__main__":
    engine = OpenAIEngine()
    
    if engine.is_available():
        result = engine.classify(
            subject="Q4 Budget Review Meeting Tomorrow",
            body="Hi team, reminder about the budget meeting tomorrow at 2pm.",
            sender="boss@company.com"
        )
