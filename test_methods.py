import requests
import json

methods = [
    "invoke", "agent.invoke", "chat", "agent.chat",
    "tasks.create", "task.create", "tasks.submit", "task.submit",
    "kagent.invoke", "kagent.chat"
]
params_list = [
    {"task": "hi"},
    {"input": "hi"},
    {"message": "hi"},
    {"agent_name": "wellness", "task": "hi"},
    {"app_name": "wellness", "task": "hi"},
    {"kagent_app_name": "default__NS__wellness", "task": "hi"},
    {"agent": "wellness", "task": "hi"}
]

url = "http://localhost:8080"
headers_list = [
    {"Host": "wellness.local", "Content-Type": "application/json"},
    {"Host": "wellness.local", "Content-Type": "application/json-rpc"}
]
jsonrpc_versions = ["2.0"]

for headers in headers_list:
    for version in jsonrpc_versions:
        for method in methods:
            for params in params_list:
                payload = {
                    "method": method,
                    "params": params,
                    "id": "1"
                }
                if version:
                    payload["jsonrpc"] = version
                
                try:
                    response = requests.post(url, json=payload, headers=headers)
                    print(f"Ver: {version}, Method: {method}, Params: {list(params.keys())[0]}, Status: {response.status_code}, Response: {response.text}")
                except Exception as e:
                    print(f"Method: {method}, Error: {e}")
