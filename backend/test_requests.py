import sys
import requests

def test_requests():
    print("Testing requests...", flush=True)
    try:
        resp = requests.get("https://www.google.com")
        print(f"Status: {resp.status_code}", flush=True)
    except Exception as e:
        print(f"Error: {e}", flush=True)

if __name__ == "__main__":
    test_requests()
