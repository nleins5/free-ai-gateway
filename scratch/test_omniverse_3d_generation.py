import json
import urllib.request
import urllib.error

url = "http://localhost:8000/v1/chat/unified"
headers = {
    "Content-Type": "application/json"
}

payload = {
    "query": "tạo cho tôi mô hình 3D quả cầu vàng xoay tròn có ánh sáng đẹp",
    "task": "omniverse"
}

data = json.dumps(payload).encode("utf-8")
req = urllib.request.Request(url, data=data, headers=headers, method="POST")

print("Testing 3D scene generation via Omniverse mode...")
try:
    with urllib.request.urlopen(req, timeout=30) as response:
        status = response.status
        body = response.read().decode("utf-8")
        print(f"HTTP Status: {status}")
        result = json.loads(body)
        print("Success!")
        print(f"Provider used: {result.get('metadata', {}).get('provider')}")
        print(f"Model used: {result.get('metadata', {}).get('model')}")
        
        answer = result.get('answer', '')
        print("\nChecking if Three.js/HTML was generated:")
        if "```html" in answer:
            print("YES! ```html block found! The UI will render this as an interactive 3D scene!")
            # Print a snippet of the html block
            start_idx = answer.find("```html")
            end_idx = answer.find("```", start_idx + 7)
            print("HTML Block snippet:\n", answer[start_idx:start_idx+300] + "...")
        else:
            print("NO! HTML block was not generated.")
            print("Full response:\n", answer)
            
except urllib.error.HTTPError as e:
    print(f"HTTP Error {e.code}: {e.read().decode('utf-8')}")
except Exception as e:
    print(f"Exception: {str(e)}")
