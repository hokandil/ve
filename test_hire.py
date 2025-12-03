import requests
import json
import uuid
import time
from jose import jwt
from datetime import datetime, timedelta

# Configuration
API_URL = "http://localhost:8000/api"
JWT_SECRET = "qSZcwl7Ft2MEd2rqmMRmWzZNNWD1y/ML+QajY4PIu17JCRbKuE/92N6+56f+Qve3fyiBoZbOtXJAsPi9xeNC9w=="
CUSTOMER_ID = "00000000-0000-0000-0000-000000000001"
CUSTOMER_EMAIL = "test.manual@example.com"

import base64

def create_test_token():
    payload = {
        "sub": CUSTOMER_ID,
        "email": CUSTOMER_EMAIL,
        "role": "authenticated",
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    # Decode the secret from Base64
    decoded_secret = base64.b64decode(JWT_SECRET)
    return jwt.encode(payload, decoded_secret, algorithm="HS256")

def test_hire_flow():
    session = requests.Session()
    
    # 1. Forge Token
    print("1. Forging Token...")
    token = create_test_token()
    headers = {"Authorization": f"Bearer {token}"}
    print("   Token created.")
    
    try:
        # 2. List Marketplace Agents to get an ID
        print("\n2. Fetching Marketplace Agents...")
        response = session.get(f"{API_URL}/marketplace/ves?status=stable", headers=headers)
        if response.status_code != 200:
            print(f"   Failed to list agents: {response.text}")
            return
            
        agents = response.json().get("items", [])
        if not agents:
            print("   No agents found in marketplace.")
            return
            
        agent_id = agents[0]["id"]
        print(f"   Found agent: {agents[0]['name']} ({agent_id})")
        
        # 3. Hire the Agent
        print(f"\n3. Hiring Agent {agent_id}...")
        hire_payload = {
            "marketplace_agent_id": agent_id,
            "persona_name": "Test Hire Manual",
            "persona_email": "test.manual.hire@testcorp.com"
        }
        
        response = session.post(f"{API_URL}/customer/ves", json=hire_payload, headers=headers)
        if response.status_code == 201:
            print("   ✅ Hire successful!")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"   ❌ Hire failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_hire_flow()
