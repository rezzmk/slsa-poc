import json
import os
from flask import Flask, request
import requests
from datetime import datetime

app = Flask(__name__)

# Configuration
WAZUH_MANAGER = os.getenv('WAZUH_MANAGER', 'wazuh.manager')
WAZUH_PORT = os.getenv('WAZUH_PORT', '55000')
WAZUH_USER = os.getenv('WAZUH_USER', 'wazuh-wui')
WAZUH_PASSWORD = os.getenv('WAZUH_PASSWORD', 'MyS3cr37P450r.*-')
LOG_FILE = '/var/ossec/logs/prometheus_alerts.log'

def send_to_wazuh(alert_data):
    """Format and send alert to Wazuh via API"""
    
    # Format the alert data for Wazuh
    wazuh_event = {
        "timestamp": datetime.utcnow().isoformat(),
        "rule": {
            "level": 10 if alert_data.get('status') == 'firing' else 5,
            "description": alert_data.get('annotations', {}).get('description', 'Prometheus Alert'),
            "id": "100000",  # Custom rule ID for Prometheus alerts
            "prometheus_alert": True
        },
        "agent": {
            "name": "prometheus",
            "id": "000"  # Internal agent ID
        },
        "manager": {
            "name": WAZUH_MANAGER
        },
        "data": {
            "alert_name": alert_data.get('labels', {}).get('alertname'),
            "severity": alert_data.get('labels', {}).get('severity'),
            "status": alert_data.get('status'),
            "attack_type": alert_data.get('labels', {}).get('attack_type', 'unknown'),
            "summary": alert_data.get('annotations', {}).get('summary'),
            "description": alert_data.get('annotations', {}).get('description')
        }
    }

    # Write to log file for Wazuh agent to pick up
    try:
        with open(LOG_FILE, 'a') as f:
            f.write(json.dumps(wazuh_event) + '\n')
    except Exception as e:
        print(f"Error writing to log file: {e}")
        return False

    return True

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming webhook from Prometheus AlertManager"""
    if request.method == 'POST':
        alerts = request.json
        
        if 'alerts' in alerts:
            for alert in alerts['alerts']:
                success = send_to_wazuh(alert)
                if not success:
                    return 'Error processing alert', 500
        
        return 'OK', 200

if __name__ == '__main__':
    # Ensure log file exists and is writable
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    open(LOG_FILE, 'a').close()
    
    app.run(host='0.0.0.0', port=5001)
