"""
Security module for scanning content and checking link safety.
"""

import re
import json
import requests
from dataclasses import dataclass
from typing import List, Dict, Optional, Set
from rich.console import Console
from rich.panel import Panel

from src.config import config

console = Console()

@dataclass
class ScanResult:
    """Result of a URL scan."""
    url: str
    is_safe: bool
    threat_type: Optional[str] = None
    
    @property
    def emoji(self) -> str:
        return "✅" if self.is_safe else "🚫"

class LinkScanner:
    """Scans text for URLs and checks their safety using remote APIs."""
    
    # Simple regex for finding URLs
    URL_PATTERN = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    
    SAFE_BROWSING_ENDPOINT = "https://safebrowsing.googleapis.com/v4/threatMatches:find"
    
    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key or config.security.safe_browsing_api_key
        if not self._api_key:
            console.print("[yellow]⚠️  No Safe Browsing API key found. Link scanning will be limited.[/yellow]")
    
    def extract_urls(self, text: str) -> List[str]:
        """Extract all URLs from a text string."""
        return list(set(re.findall(self.URL_PATTERN, text)))
    
    def scan_urls(self, urls: List[str]) -> List[ScanResult]:
        """Check a list of URLs for threats."""
        if not urls:
            return []
            
        if not self._api_key:
            # Fallback: assume all safe if no key, but print warning
            return [ScanResult(url=url, is_safe=True) for url in urls]
            
        try:
            payload = {
                "client": {
                    "clientId": "mailmind-local-assistant",
                    "clientVersion": "0.1.0"
                },
                "threatInfo": {
                    "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE", "POTENTIALLY_HARMFUL_APPLICATION"],
                    "platformTypes": ["ANY_PLATFORM"],
                    "threatEntryTypes": ["URL"],
                    "threatEntries": [{"url": url} for url in urls]
                }
            }
            
            response = requests.post(
                f"{self.SAFE_BROWSING_ENDPOINT}?key={self._api_key}",
                json=payload,
                timeout=5
            )
            
            if response.status_code != 200:
                console.print(f"[red]❌ Safe Browsing API error: {response.text}[/red]")
                return [ScanResult(url=url, is_safe=True) for url in urls]
                
            data = response.json()
            matches = data.get("matches", [])
            
            # Map matches to URLs
            threat_map: Dict[str, str] = {}
            for match in matches:
                url = match.get("threat", {}).get("url")
                threat_type = match.get("threatType")
                if url:
                    threat_map[url] = threat_type
            
            results = []
            for url in urls:
                if url in threat_map:
                    results.append(ScanResult(url=url, is_safe=False, threat_type=threat_map[url]))
                else:
                    results.append(ScanResult(url=url, is_safe=True))
                    
            return results
            
        except Exception as e:
            console.print(f"[red]❌ Link scanning failed: {e}[/red]")
            # Fail open for resilience, but log error
            return [ScanResult(url=url, is_safe=True) for url in urls]
            
    def analyze_email_content(self, body: str) -> Dict[str, any]:
        """
        Analyze email body for malicious links.
        Returns a dict with 'safe': bool, 'warnings': List[str]
        """
        urls = self.extract_urls(body)
        if not urls:
            return {"safe": True, "warnings": [], "link_count": 0}
            
        console.print(f"[cyan]🔍 Scanning {len(urls)} links...[/cyan]")
        results = self.scan_urls(urls)
        
        warnings = []
        safe = True
        
        for result in results:
            if not result.is_safe:
                safe = False
                warnings.append(f"DANGER: Malicious link found ({result.threat_type}): {result.url}")
        
        if not safe:
            console.print(Panel(
                "\n".join(warnings),
                title="[bold red]🚫 SECURITY ALERT[/bold red]",
                border_style="red"
            ))
            
        return {"safe": safe, "warnings": warnings, "link_count": len(urls)}
