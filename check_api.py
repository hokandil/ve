import requests
import json

try:
    response = requests.get("http://localhost:8000/api/marketplace/ves?status=stable")
    data = response.json()
    print(json.dumps(data, indent=2))
    
    # Check for objects in string fields
    if "items" in data:
        for item in data["items"]:
            for key, value in item.items():
                if isinstance(value, dict) and key not in ["capabilities", "tools", "labels", "annotations"]:
                    print(f"WARNING: Field '{key}' is a dict: {value}")
                if isinstance(value, list) and key not in ["tags", "screenshots", "tools"]:
                     print(f"WARNING: Field '{key}' is a list: {value}")

except Exception as e:
    print(f"Error: {e}")
