import requests
import threading
import time
from concurrent.futures import ThreadPoolExecutor

def normal_request():
    try:
        return requests.get('http://localhost:8081')
    except:
        pass

def slowloris_like():
    try:
        # Send partial request and keep connection open
        s = requests.Session()
        s.get('http://localhost:8081', stream=True)
        time.sleep(30)  # Keep connection open
    except:
        pass

def test_high_request_rate():
    """Test HighRequestRate alert - sends 1000+ requests/minute"""
    print("Testing high request rate...")
    with ThreadPoolExecutor(max_workers=50) as executor:
        for _ in range(1200):  # Slightly over threshold
            executor.submit(normal_request)
            time.sleep(0.05)  # Small delay to prevent overwhelming your machine

def test_slowloris():
    """Test SlowlorisAttack alert - many open connections, few completions"""
    print("Testing Slowloris-like behavior...")
    threads = []
    for _ in range(150):  # Create many slow connections
        t = threading.Thread(target=slowloris_like)
        threads.append(t)
        t.start()
        time.sleep(0.1)
    
    for t in threads:
        t.join()

if __name__ == "__main__":
    print("Starting DDoS simulation tests...")
    
    # Test different attack patterns
    while True:
        choice = input("""
Choose test type:
1. High Request Rate
2. Slowloris-like Attack
3. Exit
Choice: """)
        
        if choice == '1':
            test_high_request_rate()
        elif choice == '2':
            test_slowloris()
        elif choice == '3':
            break
        else:
            print("Invalid choice")
