import requests
import json
import traceback

def test_search():
    try:
        # Params matching the screenshot ID "PAR-20271205-..."
        params = {
            "destination": "Paris", 
            "depart_date": "2027-12-05",
            "return_date": "2027-12-12"
        }
        print(f"Calling API with {params}")
        r = requests.get("http://127.0.0.1:8000/travel/search", params=params, timeout=5)
        print(f"Status: {r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            print(f"Received {len(data)} offers.")
            for i, offer in enumerate(data):
                print(f"Offer {i}: {offer}")
        else:
            print(f"Error: {r.text}")

    except Exception:
        traceback.print_exc()

if __name__ == "__main__":
    test_search()
