import sys
import os
from typing import Dict, Any

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.graph import MailWorkflow
from src.core.email_client import Email
from src.core.llm import create_llm_engine, EmailCategory
from src.core.security import LinkScanner
from src.core.state import AgentState
from rich.console import Console

console = Console()

def run_real_test(name, subject, body):
    console.print(f"\n[bold blue]🚀 Running Real Test: {name}[/bold blue]")
    
    # 1. Initialize REAL components
    try:
        llm = create_llm_engine()
        if not llm.is_available():
            console.print("[yellow]⚠️  LLM provider is not available. Check your configuration/Ollama status.[/yellow]")
            return
            
        scanner = LinkScanner() # Uses REAL regex and API if key exists
        
        workflow = MailWorkflow(llm_engine=llm, scanner=scanner)
        graph = workflow.graph
        
        # 2. Prepare state
        email = Email(uid="real-test", subject=subject, sender="test@example.com", sender_name="Sender", body=body)
        initial_state = {
            "email": email,
            "classification": None,
            "security_analysis": None,
            "summary": None,
            "user_intent": "skip",
            "messages": [],
            "is_processed": False,
            "should_speak": False
        }
        
        # 3. Run graph
        console.print("[cyan]Running graph through real LLM...[/cyan]")
        result = graph.invoke(initial_state)
        
        # 4. Display results
        console.print(f"\n[bold green]Results for: {name}[/bold green]")
        console.print(f"Classification: {result.get('classification')}")
        console.print(f"Summary: {result.get('summary')}")
        
        analysis = result.get("security_analysis")
        if analysis:
            console.print(f"Security Scan: {analysis.get('link_count', 0)} links found. Safe: {analysis.get('safe')}")
        else:
            console.print("Security Scan: [yellow]SKIPPED[/yellow] (No links detected)")
            
    except Exception as e:
        console.print(f"[red]❌ Error running test: {e}[/red]")

if __name__ == "__main__":
    # Test 1: Generic Login Alert (No Links)
    body1 = "Yeni bir cihazda hesabınızda yeni bir oturum açma işlemi tespit ettik. Bu işlem size aitse herhangi bir şey yapmanız gerekmez. İşlem size ait değilse hesabınızı güven altına almanıza yardımcı oluruz."
    run_real_test("Anonymous Login Alert (No Links)", "Oturum Açma Uyarısı", body1)
    
    # Test 2: Anonymous Digest (With Links)
    body2 = """ Weekly Digest
-----
Question: Is [Amount] a good salary in [Location]?
Answer from [User]
I moved to [Location] in [Year] with a salary of [Amount]...
Read More:
https://example.com/digest/article-123"""
    run_real_test("Anonymous Digest (With Links)", "Weekly Digest", body2)
