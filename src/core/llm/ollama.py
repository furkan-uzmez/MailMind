"""
Ollama LLM provider for local inference.
Uses the ollama Python library to communicate with local Ollama server.
"""

import json
import re
from typing import Optional

import ollama
from rich.console import Console
from rich.panel import Panel

from .base import BaseLLMEngine, ClassificationResult, EmailCategory
from src.config import config

console = Console()


class OllamaEngine(BaseLLMEngine):
    """Ollama-based LLM engine for local inference."""
    
    def __init__(self, model: Optional[str] = None, host: Optional[str] = None):
        self._model = model or config.ollama.model
        self._host = host or config.ollama.host
        
    @property
    def provider_name(self) -> str:
        return "ollama"
    
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

    def classify(self, subject: str, body: str, sender: str = "") -> ClassificationResult:
        """Classify an email into IMPORTANT, NEWSLETTER, or SPAM."""
        email_text = f"""From: {sender}
Subject: {subject}

{body[:1500]}"""

        console.print("[cyan]🤖 Classifying email (Ollama)...[/cyan]")
        
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
            title="Classification",
            border_style="cyan"
        ))
        
        return result
    
    def summarize(self, subject: str, body: str) -> str:
        """Summarize an email into 1-2 sentences."""
        email_text = f"""Subject: {subject}

{body[:1500]}"""

        console.print("[cyan]🤖 Summarizing (Ollama)...[/cyan]")
        
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

        console.print("[cyan]🤖 Drafting reply (Ollama)...[/cyan]")
        
        reply = self._call(self.REPLY_PROMPT, prompt, temperature=0.5)
        
        if reply:
            console.print(Panel(reply, title="Draft Reply", border_style="blue"))
        
        return reply
    
    def ask(self, question: str, email_context: str) -> str:
        """Answer a question about emails."""
        prompt = f"""Email Context:
{email_context[:2000]}

Question: {question}"""

        console.print("[cyan]🤖 Thinking (Ollama)...[/cyan]")
        
        answer = self._call(self.QA_PROMPT, prompt, temperature=0.4)
        
        if answer:
            console.print(Panel(answer, title="Answer", border_style="magenta"))
        
        return answer


# Quick test
if __name__ == "__main__":
    engine = OllamaEngine()
    
    if engine.is_available():
        result = engine.classify(
            subject="Q4 Budget Review Meeting Tomorrow",
            body="Hi team, reminder about the budget meeting tomorrow at 2pm.",
            sender="boss@company.com"
        )
