from typing import Any, Dict, Literal, Optional

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage

from src.core.state import AgentState
from src.core.llm import EmailCategory, ClassificationResult
from src.core.email_client import Email
from rich.console import Console

console = Console()

class MailWorkflow:
    def __init__(self, llm_engine, scanner, tts_engine=None, stt_engine=None):
        self.llm = llm_engine
        self.scanner = scanner
        self.tts = tts_engine
        self.stt = stt_engine
        
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(AgentState)

        # 1. Add Nodes
        workflow.add_node("classify", self.classify_email)
        workflow.add_node("security_scan", self.scan_security)
        workflow.add_node("summarize", self.summarize_email)
        workflow.add_node("speak_summary", self.read_summary)
        workflow.add_node("wait_for_input", self.wait_for_user_input)
        workflow.add_node("process_intent", self.process_user_intent)
        workflow.add_node("draft_reply", self.draft_reply)
        workflow.add_node("answer_question", self.answer_question)

        # 2. Add Edges
        workflow.set_entry_point("classify")
        
        workflow.add_conditional_edges(
            "classify",
            self.check_for_links,
            {
                "scan": "security_scan",
                "skip": "summarize"
            }
        )
        workflow.add_edge("security_scan", "summarize")
        workflow.add_edge("summarize", "speak_summary")
        
        workflow.add_conditional_edges(
            "speak_summary",
            self.should_listen,
            {
                "listen": "wait_for_input",
                "done": END
            }
        )
        
        workflow.add_conditional_edges(
            "wait_for_input",
            self.check_input_received,
            {
                "process": "process_intent",
                "done": END
            }
        )
        
        workflow.add_conditional_edges(
            "process_intent",
            lambda x: x["user_intent"],
            {
                "reply": "draft_reply",
                "question": "answer_question",
                "skip": END,
                "repeat": "speak_summary",
                "unknown": "wait_for_input" 
            }
        )
        
        workflow.add_edge("draft_reply", "wait_for_input")
        workflow.add_edge("answer_question", "wait_for_input")

        return workflow.compile()

    # --- Node Implementations ---

    def check_for_links(self, state: AgentState) -> Literal["scan", "skip"]:
        # console.print("[dim]DEBUG: check_for_links[/dim]")
        email = state["email"]
        urls = self.scanner.extract_urls(email.body)
        if urls:
            return "scan"
        return "skip"

    def classify_email(self, state: AgentState) -> Dict[str, Any]:
        # console.print("[dim]DEBUG: classify[/dim]")
        email = state["email"]
        classification = self.llm.classify(
            subject=email.subject,
            body=email.body,
            sender=email.sender
        )
        return {"classification": classification}

    def scan_security(self, state: AgentState) -> Dict[str, Any]:
        # console.print("[dim]DEBUG: scan_security[/dim]")
        email = state["email"]
        analysis = self.scanner.analyze_email_content(email.body)
        
        updates = {"security_analysis": analysis}
        
        if not analysis["safe"]:
             current_class = state.get("classification")
             warnings = analysis.get("warnings", [])
             warning_msg = warnings[0] if warnings else "Unknown Threat"
             
             if current_class and current_class.category != EmailCategory.SPAM:
                 updates["classification"] = ClassificationResult(
                     category=EmailCategory.SPAM,
                     reason=f"Security Threat Detected: {warning_msg}"
                 )
        
        return updates

    def summarize_email(self, state: AgentState) -> Dict[str, Any]:
        # console.print("[dim]DEBUG: summarize[/dim]")
        email = state["email"]
        analysis = state.get("security_analysis") or {}
        
        context_prefix = ""
        if not analysis.get("safe", True):
            warnings = analysis.get("warnings", [])
            context_prefix = "SECURITY WARNING: " + "; ".join(warnings) + "\n\n"
        elif analysis.get("link_count", 0) > 0:
            context_prefix = f"Security Check: {analysis['link_count']} links found. All links appear SAFE.\n\n"
            
        summary_body = context_prefix + email.body
        summary = self.llm.summarize(subject=email.subject, body=summary_body)
        return {"summary": summary}

    def read_summary(self, state: AgentState) -> Dict[str, Any]:
        # console.print("[dim]DEBUG: read_summary[/dim]")
        if not self.tts:
            return {}
            
        summary = state["summary"]
        email = state["email"]
        classification = state["classification"]
        
        category_name = classification.category.value.lower()
        text_to_speak = f"{category_name} email from {email.sender_name}. {summary}"
        
        self.tts.speak(text_to_speak)
        return {"should_speak": False}

    def should_listen(self, state: AgentState) -> Literal["listen", "done"]:
        if self.stt:
            return "listen"
        return "done"
        
    def check_input_received(self, state: AgentState) -> Literal["process", "done"]:
        # If user_intent is explicitly skip, we are done
        if state.get("user_intent") == "skip":
            return "done"
        return "process"

    def wait_for_user_input(self, state: AgentState) -> Dict[str, Any]:
        # console.print("[dim]DEBUG: wait_for_user_input[/dim]")
        print("\n[bold cyan]💬 What would you like to do?[/bold cyan]")
        print("[dim]Say: 'reply', 'skip', 'read again', or ask a question[/dim]")
        
        updates = {"user_intent": None}
        
        if not self.stt:
            updates["user_intent"] = "skip"
            return updates

        command = self.stt.listen()
        if not command:
            updates["user_intent"] = "skip"
            return updates
            
        updates["messages"] = [HumanMessage(content=command)]
        return updates

    def process_user_intent(self, state: AgentState) -> Dict[str, Any]:
        # console.print("[dim]DEBUG: process_user_intent[/dim]")
        messages = state.get("messages", [])
        if not messages:
            return {"user_intent": "skip"}
            
        last_message = messages[-1]
        command = last_message.content.lower()
        
        if "skip" in command or "next" in command:
            return {"user_intent": "skip"}
        
        if "read again" in command or "repeat" in command:
            return {"user_intent": "repeat"}
            
        if "reply" in command:
            return {"user_intent": "reply"}
            
        return {"user_intent": "question"}

    def draft_reply(self, state: AgentState) -> Dict[str, Any]:
        if not self.stt or not self.tts:
            return {}
            
        print("[cyan]What would you like to say?[/cyan]")
        intent = self.stt.listen()
        
        if intent:
            email = state["email"]
            email_context = f"From: {email.sender}\nSubject: {email.subject}\n\n{email.body}"
            reply = self.llm.draft_reply(email_context, intent)
            
            if reply:
                self.tts.speak(f"Here's the draft: {reply}")
                return {"messages": [AIMessage(content=f"Draft: {reply}")]}
        
        return {}

    def answer_question(self, state: AgentState) -> Dict[str, Any]:
        messages = state.get("messages", [])
        if not messages:
            return {}
            
        last_msg = messages[-1]
        question = last_msg.content
        
        email = state["email"]
        email_context = f"From: {email.sender}\nSubject: {email.subject}\n\n{email.body}"
        
        answer = self.llm.ask(question, email_context)
        
        if answer and self.tts:
            self.tts.speak(answer)
            return {"messages": [AIMessage(content=answer)]}
            
        return {}
