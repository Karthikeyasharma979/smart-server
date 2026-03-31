import requests

def test_extract(url_to_test):
    api_url = "http://localhost:4000/extract-url"
    payload = {
        "url": url_to_test
    }
    
    try:
        print(f"Testing URL: {url_to_test}")
        response = requests.post(api_url, json=payload)
        response.raise_for_status()
        data = response.json()
        
        if data.get('success'):
            print("SUCCESS: URL Extraction API works!")
            text = data.get('text', '')
            print(f"Extracted text length: {len(text)}")
            print("Preview (first 1000 chars):")
            print(text[:1000])
            if len(text) > 2000:
                print("\n--- Middle Chunk ---")
                print(text[1000:2000])
        else:
            print("ERROR: API returned an error:", data.get('error'))
            
    except Exception as e:
        print("ERROR: Request failed:", str(e))

if __name__ == "__main__":
    # Test with a Wikipedia article as a standard baseline
    test_extract("https://en.wikipedia.org/wiki/Artificial_intelligence")
