from flask import Flask, request
import logging
import sys

app = Flask(__name__)

# Configure logging to write to a file or syslog
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[logging.FileHandler('/app/logs/alertmanager_to_wazuh.log')]
)

@app.route('/alert', methods=['POST'])
def alert():
    alert_data = request.get_json()
    # Format the alert data as needed for Wazuh
    formatted_alert = format_alert(alert_data)
    # Log the alert (Wazuh will monitor this log file)
    logging.info(formatted_alert)
    return '', 200

def format_alert(alert):
    # Extract relevant information from the alert
    alerts = alert.get('alerts', [])
    formatted_alerts = []
    for a in alerts:
        status = a.get('status')
        labels = a.get('labels', {})
        annotations = a.get('annotations', {})
        summary = annotations.get('summary', 'No summary')
        attack_type = labels.get('attack_type', 'unknown')
        ip_addr = labels.get('client_ip_address', 'unknown')
        # Create a log entry
        log_entry = f"Alertmanager Alert - Status: {status}, AttackType: {attack_type}, SourceIp: {ip_addr}, Labels: {labels}"
        formatted_alerts.append(log_entry)
    return '\n'.join(formatted_alerts)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
