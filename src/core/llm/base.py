"""
Abstract base class for LLM providers.
Defines the contract that all LLM implementations must follow.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional


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


class BaseLLMEngine(ABC):
    """
    Abstract base class for LLM engines.
    
    All LLM providers (Ollama, OpenAI, Anthropic, etc.) must implement this interface.
    This enables easy swapping between local and cloud providers.
    """
    
    # Standard prompts that providers can use
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

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the name of this provider (e.g., 'ollama', 'openai')."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is available and configured."""
        pass
    
    @abstractmethod
    def classify(self, subject: str, body: str, sender: str = "") -> ClassificationResult:
        """
        Classify an email into IMPORTANT, NEWSLETTER, or SPAM.
        
        Args:
            subject: Email subject line
            body: Email body text
            sender: Sender email address
            
        Returns:
            ClassificationResult with category and reasoning
        """
        pass
    
    @abstractmethod
    def summarize(self, subject: str, body: str) -> str:
        """
        Summarize an email into 1-2 sentences.
        
        Args:
            subject: Email subject line
            body: Email body text
            
        Returns:
            Concise summary string
        """
        pass
    
    @abstractmethod
    def draft_reply(self, original_email: str, user_intent: str) -> str:
        """
        Draft a reply based on user's intent.
        
        Args:
            original_email: The email being replied to
            user_intent: What the user wants to say
            
        Returns:
            Draft reply text
        """
        pass
    
    @abstractmethod
    def ask(self, question: str, email_context: str) -> str:
        """
        Answer a question about emails.
        
        Args:
            question: User's question
            email_context: Relevant email content
            
        Returns:
            Answer string
        """
        pass
