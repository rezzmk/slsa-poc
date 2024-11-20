from flask import Flask, request, jsonify
import json
import requests
import socket
import os
from datetime import datetime
from functools import wraps
import urllib3

# Disable SSL warnings for development
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

class WazuhAuth:
    def __init__(self):
        self.wazuh_manager = os.getenv('WAZUH_MANAGER', 'wazuh.manager')
        self.api_user = os.getenv('WAZUH_API_USER', 'wazuh-wui')
        self.api_password = os.getenv('WAZUH_API_PASSWORD', 'MyS3cr37P450r.*-')
        self.token = None
        self.base_url = f'https://{self.wazuh_manager}:55000'

    def get_token(self):
        if self.token is not None:
            return self.token

        try:
            auth_url = f"{self.base_url}/security/user/authenticate"
            response = requests.get(
                auth_url,
                auth=(self.api_user, self.api_password),
                verify=False  # In production, use proper cert verification
            )
            
            if response.status_code == 200:
                self.token = response.json()['data']['token']
                return self.token
            else:
                app.logger.error(f"Authentication failed: {response.text}")
                return None
        except Exception as e:
            app.logger.error(f"Error getting token: {str(e)}")
            return None

wazuh_auth = WazuhAuth()

def require_wazuh_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Missing authorization header'}), 401

        expected_token = wazuh_auth.get_token()
        if not expected_token:
            return jsonify({'error': 'Failed to authenticate with Wazuh'}), 500

        received_token = auth_header.replace('Bearer ', '')
        if received_token != expected_token:
            return jsonify({'error': 'Invalid token'}), 403

        return f(*args, **kwargs)
    return decorated

def send_to_wazuh(message):
    """Send event to Wazuh manager"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        wazuh_message = f'1:prometheus_alerts:{message}'
        sock.sendto(wazuh_message.encode(), (wazuh_auth.wazuh_manager, 1514))
        sock.close()
        return True
    except Exception as e:
        app.logger.error(f"Error sending to Wazuh: {str(e)}")
        return False

@app.route('/auth', methods=['GET'])
def get_auth_token():
    """Endpoint for Alertmanager to get the current token"""
    token = wazuh_auth.get_token()
    if token:
        return jsonify({'token': token})
    return jsonify({'error': 'Failed to get token'}), 500

@app.route('/webhook', methods=['POST'])
@require_wazuh_auth
def webhook():
    if not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 400

    try:
        content = request.json
        for alert in content.get('alerts', []):
            alert_data = {
                'alertname': alert.get('labels', {}).get('alertname'),
                'severity': alert.get('labels', {}).get('severity'),
                'status': alert.get('status'),
                'description': alert.get('annotations', {}).get('description'),
                'timestamp': datetime.now().isoformat(),
                'prometheus_fingerprint': alert.get('fingerprint'),
                'attack_type': alert.get('labels', {}).get('attack_type', 'unknown')
            }
            
            if not send_to_wazuh(json.dumps(alert_data)):
                return jsonify({'error': 'Failed to send alert to Wazuh'}), 500

        return jsonify({'status': 'success'}), 200
    except Exception as e:
        app.logger.error(f"Error processing webhook: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9093)
