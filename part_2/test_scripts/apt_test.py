import requests
import time
import random
from concurrent.futures import ThreadPoolExecutor
import argparse

def simulate_reconnaissance(base_url):
    """Simulate slow probing and scanning"""
    print("Starting reconnaissance phase...")
    paths = ['/api/admin', '/api/users', '/api/config', '/api/system', '/api/data']
    
    for _ in range(20):  # More attempts to trigger alerts
        path = random.choice(paths)
        try:
            response = requests.get(f'{base_url}{path}')
            print(f"Reconnaissance: {path} - Status: {response.status_code}")
            # Sleep between 1 to 3 seconds to simulate slow probing
            time.sleep(random.uniform(1, 3))
        except Exception as e:
            print(f"Error during reconnaissance: {e}")

def simulate_c2_beaconing(base_url):
    """Simulate C2 beaconing with low volume, regular traffic"""
    print("Starting C2 beaconing simulation...")
    
    for _ in range(30):  # Extended duration to trigger alerts
        try:
            # Small payload to simulate beaconing
            payload = {'data': 'beacon_data'}
            response = requests.post(f'{base_url}/api/beacon', json=payload)
            print(f"C2 Beacon - Status: {response.status_code}")
            # Regular intervals between 5-10 seconds
            time.sleep(random.uniform(5, 10))
        except Exception as e:
            print(f"Error during C2 beaconing: {e}")

def simulate_data_exfiltration(base_url):
    """Simulate data exfiltration with large response sizes"""
    print("Starting data exfiltration simulation...")
    
    for _ in range(10):  # Multiple large requests
        size = 1024 * 1024 * 2  # 2MB of data
        try:
            response = requests.get(f'{base_url}/api/data?size={size}')
            print(f"Data Exfiltration - Status: {response.status_code} - Size requested: {size}")
            time.sleep(2)
        except Exception as e:
            print(f"Error during data exfiltration: {e}")

def simulate_persistence(base_url):
    """Simulate persistence with off-hours activity"""
    print("Starting persistence simulation...")
    
    for _ in range(20):
        paths = ['/api/status', '/api/data', '/api/config']
        path = random.choice(paths)
        try:
            response = requests.get(f'{base_url}{path}')
            print(f"Persistence Check - Path: {path} - Status: {response.status_code}")
            time.sleep(random.uniform(2, 4))
        except Exception as e:
            print(f"Error during persistence check: {e}")

def main():
    parser = argparse.ArgumentParser(description='APT Attack Simulation')
    parser.add_argument('--url', default='http://localhost:8081', help='Base URL of the target service')
    parser.add_argument('--phase', choices=['recon', 'c2', 'exfil', 'persist', 'all'], default='all', help='Attack phase to simulate')
    
    args = parser.parse_args()

    if args.phase == 'recon' or args.phase == 'all':
        simulate_reconnaissance(args.url)
        
    if args.phase == 'c2' or args.phase == 'all':
        simulate_c2_beaconing(args.url)
        
    if args.phase == 'exfil' or args.phase == 'all':
        simulate_data_exfiltration(args.url)
        
    if args.phase == 'persist' or args.phase == 'all':
        simulate_persistence(args.url)

if __name__ == "__main__":
    main()
