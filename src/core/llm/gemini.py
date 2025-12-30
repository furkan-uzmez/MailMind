"""
Google Gemini LLM provider implementation.
"""

import json
import os
from typing import Optional

try:
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
except ImportError:
    genai = None

from rich.console import Console
from rich.panel import Panel

from .base import BaseLLMEngine, ClassificationResult, EmailCategory

console = Console()


class GeminiEngine(BaseLLMEngine):
    """Google Gemini LLM engine."""
    
    def __init__(self, **kwargs):
        if not genai:
            raise ImportError(
                "google-generativeai package is required. "
                "Install it with: pip install google-generativeai"
            )
            
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is not set")
            
        genai.configure(api_key=api_key)
        
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-pro")
        self.model = genai.GenerativeModel(self.model_name)
        
        # Safety settings - block only high probability harmful content
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
        }

    @property
    def provider_name(self) -> str:
        return "gemini"

    def is_available(self) -> bool:
        return bool(os.getenv("GOOGLE_API_KEY"))

    def _generate(self, prompt: str) -> str:
        """Helper to generate text with error handling."""
        try:
            response = self.model.generate_content(
                prompt,
                safety_settings=self.safety_settings
            )
            return response.text
        except Exception as e:
            return f"Error generating response: {str(e)}"

    def classify(self, subject: str, body: str, sender: str = "") -> ClassificationResult:
        console.print("[cyan]🤖 Classifying email (Gemini)...[/cyan]")

        prompt = f"""{self.CLASSIFIER_PROMPT}

Email to classify:
From: {sender}
Subject: {subject}
Body:
{body[:2000]}  # Truncate long emails
"""
        response_text = self._generate(prompt)
        
        try:
            # Clean up response if it contains markdown code blocks
            clean_text = response_text.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_text)
            
            category = EmailCategory(data["category"])
            reason = data["reason"]
            
            result = ClassificationResult(
                category=category,
                reason=reason,
                confidence=0.9
            )
            
            console.print(Panel(
                f"[bold]{result.emoji} {category.value}[/bold]\n[dim]{reason}[/dim]",
                title="Classification",
                border_style="cyan"
            ))
            
            return result
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            # Fallback for parsing errors
            return ClassificationResult(
                category=EmailCategory.IMPORTANT,
                reason=f"Failed to parse classification: {str(e)}",
                confidence=0.0
            )

    def summarize(self, subject: str, body: str) -> str:
        console.print("[cyan]🤖 Summarizing (Gemini)...[/cyan]")

        prompt = f"""{self.SUMMARIZER_PROMPT}

Email to summarize:
Subject: {subject}
Body:
{body[:4000]}
"""
        summary = self._generate(prompt).strip()
        
        if summary:
            console.print(Panel(summary, title="Summary", border_style="green"))
            
        return summary

    def draft_reply(self, original_email: str, user_intent: str) -> str:
        console.print("[cyan]🤖 Drafting reply (Gemini)...[/cyan]")

        prompt = f"""{self.REPLY_PROMPT}

Original Email:
{original_email[:2000]}

User Intent:
{user_intent}
"""
        reply = self._generate(prompt).strip()
        
        if reply:
            console.print(Panel(reply, title="Draft Reply", border_style="blue"))
            
        return reply

    def ask(self, question: str, email_context: str) -> str:
        console.print("[cyan]🤖 Thinking (Gemini)...[/cyan]")

        prompt = f"""{self.QA_PROMPT}

Email Context:
{email_context[:4000]}

Question:
{question}
"""
        answer = self._generate(prompt).strip()
        
        if answer:
            console.print(Panel(answer, title="Answer", border_style="magenta"))
            
        return answer
