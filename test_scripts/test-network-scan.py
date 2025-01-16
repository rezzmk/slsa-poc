import requests
import time
from concurrent.futures import ThreadPoolExecutor

def scan_endpoint(url):
    try:
        response = requests.get(url, timeout=1)
        print(f"{url} -> {response.status_code}")
        return response.status_code
    except Exception as e:
        print(f"{url} -> error: {e}")
        return None

def main():
    # Target service
    base_urls = [
        "http://localhost:8081",
        "http://localhost:8082",
        "http://localhost:8083"
    ]
    
    # Endpoints to scan
    endpoints = [
        '/api/admin',
        '/api/config',
        '/api/users',
        '/api/data',
        '/api/nonexistent',
        '/api/test/123',
        '/api/v1/secret',
        '/api/v2/admin',
        '/admin',
        '/config',
        '/test'
    ]

    # Generate all URLs to scan
    urls = []
    for base_url in base_urls:
        for endpoint in endpoints:
            urls.extend([f"{base_url}{endpoint}" for _ in range(3)])  # Repeat each 3 times

    print(f"Starting aggressive scan of {len(urls)} endpoints...")
    
    # Scan with multiple threads
    with ThreadPoolExecutor(max_workers=10) as executor:
        for i in range(3):  # Do 3 rounds
            print(f"\nRound {i+1}")
            futures = [executor.submit(scan_endpoint, url) for url in urls]
            for future in futures:
                try:
                    future.result()
                except Exception as e:
                    print(f"Error: {e}")
            time.sleep(1)  # Brief pause between rounds

if __name__ == "__main__":
    main()
