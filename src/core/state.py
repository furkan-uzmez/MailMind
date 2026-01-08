from typing import TypedDict, Optional, List, Any
from langchain_core.messages import BaseMessage

from src.core.email_client import Email
from src.core.llm import ClassificationResult

class AgentState(TypedDict):
    """
    Represents the state of the email processing agent.
    """
    email: Email
    classification: Optional[ClassificationResult]
    security_analysis: Optional[dict[str, Any]]
    summary: Optional[str]
    
    # Conversation state
    user_intent: Optional[str]
    messages: List[BaseMessage]
    
    # Flags
    is_processed: bool
    should_speak: bool
