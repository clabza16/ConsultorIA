import subprocess
import json
import os

def call_mcp(stdin, stdout, method, params=None):
    request = {
        "jsonrpc": "2.0",
        "method": method,
        "id": os.getpid() + hash(method) % 1000
    }
    if params is not None:
        request["params"] = params
    
    stdin.write(json.dumps(request) + '\n')
    stdin.flush()
    line = stdout.readline()
    return line

try:
    p = subprocess.Popen(['notebooklm-mcp'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdin_pipe = p.stdin
    stdout_pipe = p.stdout
    
    # 1. Initialize
    init_params = {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "test-client", "version": "1.0.0"}
    }
    call_mcp(stdin_pipe, stdout_pipe, "initialize", init_params)
    
    # 2. Notifications (initialized)
    stdin_pipe.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + '\n')
    stdin_pipe.flush()
    
    # 3. Call notebook_list
    print("Listing Notebooks...")
    result_json = call_mcp(stdin_pipe, stdout_pipe, "tools/call", {"name": "notebook_list", "arguments": {}})
    data = json.loads(result_json)
    
    if "result" in data and "content" in data["result"]:
        for item in data["result"]["content"]:
            if item["type"] == "text":
                print(item["text"])
    else:
        print("Error or no content found:", result_json)
    
except Exception as e:
    print(f"Error: {e}")
finally:
    if 'p' in locals():
        p.terminate()
