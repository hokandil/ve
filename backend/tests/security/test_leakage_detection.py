"""
Penetration Test: Leakage Detection
Simulates adversarial scenarios to verify leakage detection
"""
import pytest
from app.security.leakage_detector import leakage_detector

@pytest.mark.security
class TestLeakageDetection:
    """Penetration tests for leakage detection"""
    
    def test_detect_pii_leakage(self):
        """Test detection of PII (email)"""
        content = "Here is the user's email: user@example.com"
        customer_id = "customer-123"
        
        alerts = leakage_detector.scan(content, customer_id)
        
        assert len(alerts) > 0
        assert any(a.type == "pii" for a in alerts)
        assert any(a.severity == "medium" for a in alerts)
    
    def test_detect_cross_customer_leakage(self):
        """Test detection of foreign UUIDs"""
        current_customer = "11111111-1111-1111-1111-111111111111"
        other_customer = "22222222-2222-2222-2222-222222222222"
        
        content = f"I found data for customer {other_customer}"
        
        alerts = leakage_detector.scan(content, current_customer)
        
        assert len(alerts) > 0
        assert any(a.type == "cross_customer" for a in alerts)
        assert any(a.severity == "high" for a in alerts)
        
    def test_allow_own_customer_id(self):
        """Test that mentioning own customer ID is allowed"""
        current_customer = "11111111-1111-1111-1111-111111111111"
        
        content = f"Your customer ID is {current_customer}"
        
        alerts = leakage_detector.scan(content, current_customer)
        
        # Should NOT trigger cross-customer alert
        assert not any(a.type == "cross_customer" for a in alerts)

    def test_detect_api_keys(self):
        """Test detection of API keys"""
        content = "Here is the key: sk-abcdef1234567890abcdef1234567890"
        customer_id = "customer-123"
        
        alerts = leakage_detector.scan(content, customer_id)
        
        assert len(alerts) > 0
        assert any(a.type == "secret" for a in alerts)
        assert any(a.severity == "critical" for a in alerts)

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "security"])
