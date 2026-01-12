import sys
import os
from unittest.mock import MagicMock
from typing import Dict, Any

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.graph import MailWorkflow
from src.core.email_client import Email
from src.core.llm import EmailCategory, ClassificationResult
from src.core.state import AgentState

def test_flow_no_links():
    print("\n--- Testing Flow: No Links ---")
    
    # Mock dependencies
    llm = MagicMock()
    llm.classify.return_value = ClassificationResult(category=EmailCategory.IMPORTANT, reason="Test")
    llm.summarize.return_value = "This is a summary."
    
    scanner = MagicMock()
    scanner.extract_urls.return_value = [] # NO LINKS
    scanner.analyze_email_content.return_value = {"safe": True, "warnings": [], "link_count": 0}
    
    workflow = MailWorkflow(llm_engine=llm, scanner=scanner)
    graph = workflow.graph
    
    # Initial state
    email = Email(uid="1", subject="Oturum Açma Uyarısı", sender="security@example.com", sender_name="Güvenlik Ekibi", body="Yeni bir cihazda hesabınızda yeni bir oturum açma işlemi tespit ettik. Bu işlem size aitse herhangi bir şey yapmanız gerekmez. İşlem size ait değilse hesabınızı güven altına almanıza yardımcı oluruz.")
    initial_state = {
        "email": email,
        "classification": None,
        "security_analysis": None,
        "summary": None,
        "user_intent": "skip", # To end the flow quickly
        "messages": [],
        "is_processed": False,
        "should_speak": False
    }
    
    # Run graph
    print("Running graph...")
    result = graph.invoke(initial_state)
    
    print(f"Classification: {result.get('classification')}")
    print(f"Summary: {result.get('summary')}")
    
    # Verify scanner.analyze_email_content was NOT called
    if scanner.analyze_email_content.called:
        print("❌ FAILED: security_scan node was entered!")
        return False
    else:
        print("✅ SUCCESS: security_scan node was skipped.")
        return True

def test_flow_with_links():
    print("\n--- Testing Flow: With Links ---")
    
    # Mock dependencies
    llm = MagicMock()
    llm.classify.return_value = ClassificationResult(category=EmailCategory.IMPORTANT, reason="Test")
    llm.summarize.return_value = "This is a summary."
    
    scanner = MagicMock()
    scanner.extract_urls.return_value = ["https://example.com/read-more"] # HAS LINKS
    scanner.analyze_email_content.return_value = {"safe": True, "warnings": [], "link_count": 1}
    
    workflow = MailWorkflow(llm_engine=llm, scanner=scanner)
    graph = workflow.graph
    
    # Initial state
    email = Email(uid="1", subject="Daily Digest", sender="newsletter@example.com", sender_name="Digest Team", body=""" Weekly Digest
-----
Question: Is [Amount] a good salary in [Location]?
Answer from [User]
I moved to [Location] in [Year]...
Read More:
https://example.com/read-more""")

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
    
    # Run graph
    print("Running graph...")
    result = graph.invoke(initial_state)
    
    print(f"Classification: {result.get('classification')}")
    print(f"Summary: {result.get('summary')}")
    
    # Verify scanner.analyze_email_content WAS called
    if scanner.analyze_email_content.called:
        print("✅ SUCCESS: security_scan node was entered.")
        return True
    else:
        print("❌ FAILED: security_scan node was NOT entered!")
        return False

if __name__ == "__main__":
    s1 = test_flow_no_links()
    s2 = test_flow_with_links()
    
    if s1 and s2:
        print("\n🎉 ALL TESTS PASSED!")
        sys.exit(0)
    else:
        print("\n❌ SOME TESTS FAILED!")
        sys.exit(1)
