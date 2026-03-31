import requests

def test_search():
    url = "http://localhost:4000/search"
    payload = {
        "query": "React boilerplate",
        "max_results": 2
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        
        if data.get('success'):
            print("✅ Web Search API works! Results:")
            for idx, res in enumerate(data.get('results', [])):
                print(f"\n{idx + 1}. {res.get('title')}")
                print(f"   Link: {res.get('href')}")
                print(f"   Snippet: {res.get('body')}")
        else:
            print("❌ API returned an error:", data.get('error'))
            
    except Exception as e:
        print("❌ Request failed:", str(e))

if __name__ == "__main__":
    test_search()
