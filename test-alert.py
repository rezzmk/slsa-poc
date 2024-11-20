import requests
import json

def send_test_alert():
    webhook_url = "http://localhost:5001/webhook"
    
    # Sample alert payload
    payload = {
        "alerts": [{
            "status": "firing",
            "labels": {
                "alertname": "TestAlert",
                "severity": "critical",
                "attack_type": "test"
            },
            "annotations": {
                "description": "This is a test alert",
                "summary": "Test Alert Summary"
            },
            "startsAt": "2024-11-20T10:00:00Z"
        }]
    }
    
    try:
        response = requests.post(webhook_url, json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    send_test_alert()
