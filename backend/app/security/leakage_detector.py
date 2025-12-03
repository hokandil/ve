"""
Context Leakage Detector
Monitors agent outputs for potential data leakage and PII
"""
import re
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class LeakageAlert:
    severity: str  # low, medium, high, critical
    type: str      # pii, cross_customer, secret
    description: str
    timestamp: str
    context: Dict[str, Any]

class ContextLeakageDetector:
    """
    Analyzes content for potential security leakage.
    
    Checks for:
    1. PII (Email, Phone, SSN)
    2. Cross-customer data leakage (Customer IDs)
    3. Secrets (API keys, tokens)
    """
    
    # Regex patterns for detection
    PATTERNS = {
        "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
        "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
        "uuid": r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
        "api_key": r"sk-[a-zA-Z0-9]{32,}",
        "jwt": r"eyJ[a-zA-Z0-9_-]{10,}\.eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}"
    }
    
    def __init__(self):
        self.alerts: List[LeakageAlert] = []
    
    def scan(
        self,
        content: str,
        customer_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[LeakageAlert]:
        """
        Scan content for leakage
        
        Args:
            content: Text to scan
            customer_id: Current customer ID (to whitelist)
            metadata: Additional context
            
        Returns:
            List of alerts found
        """
        alerts = []
        
        # 1. Check for PII
        if self._contains_pii(content):
            alerts.append(LeakageAlert(
                severity="medium",
                type="pii",
                description="Potential PII detected in output",
                timestamp=datetime.utcnow().isoformat(),
                context={"content_snippet": content[:50] + "..."}
            ))
            
        # 2. Check for Secrets
        if self._contains_secrets(content):
            alerts.append(LeakageAlert(
                severity="critical",
                type="secret",
                description="Potential API key or token detected",
                timestamp=datetime.utcnow().isoformat(),
                context={"content_snippet": "REDACTED"}
            ))
            
        # 3. Check for Cross-Customer Leakage
        # Detect UUIDs that are NOT the current customer_id
        other_uuids = self._find_other_uuids(content, customer_id)
        if other_uuids:
            alerts.append(LeakageAlert(
                severity="high",
                type="cross_customer",
                description=f"Potential cross-customer leakage: Found {len(other_uuids)} foreign UUIDs",
                timestamp=datetime.utcnow().isoformat(),
                context={"uuids": other_uuids}
            ))
            
        # Log alerts
        for alert in alerts:
            logger.warning(
                f"SECURITY ALERT [{alert.severity}]: {alert.description} "
                f"(Customer: {customer_id})"
            )
            
        return alerts
    
    def _contains_pii(self, content: str) -> bool:
        """Check for PII patterns"""
        # Simple check - in production use NLP/NER
        return (
            bool(re.search(self.PATTERNS["email"], content)) or
            bool(re.search(self.PATTERNS["phone"], content)) or
            bool(re.search(self.PATTERNS["ssn"], content))
        )
    
    def _contains_secrets(self, content: str) -> bool:
        """Check for secret patterns"""
        return (
            bool(re.search(self.PATTERNS["api_key"], content)) or
            bool(re.search(self.PATTERNS["jwt"], content))
        )
    
    def _find_other_uuids(self, content: str, current_customer_id: str) -> List[str]:
        """Find UUIDs that don't match the current customer"""
        found_uuids = re.findall(self.PATTERNS["uuid"], content)
        # Filter out current customer ID
        return [uid for uid in found_uuids if uid != current_customer_id]

# Singleton
leakage_detector = ContextLeakageDetector()
