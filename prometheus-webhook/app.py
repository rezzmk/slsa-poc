from flask import Flask, request
import logging
import sys
import os

app = Flask(__name__)

# Configure service-specific loggers
service_loggers = {}
services = ['dotnet-ws1', 'dotnet-ws2', 'dotnet-ws3']

# Create loggers for each service
for service in services:
    logger = logging.getLogger(service)
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(f'/app/logs/alertmanager_{service}.log')
    handler.setFormatter(logging.Formatter('%(message)s'))
    logger.addHandler(handler)
    service_loggers[service] = logger  # Add logger to dictionary

# Main logger for all alerts
main_logger = logging.getLogger('main')
main_logger.setLevel(logging.INFO)
main_handler = logging.FileHandler('/app/logs/alertmanager_to_wazuh.log')
main_handler.setFormatter(logging.Formatter('%(message)s'))
main_logger.addHandler(main_handler)

@app.route('/alert', methods=['POST'])
def alert():
    alert_data = request.get_json()
    process_alerts(alert_data)
    return '', 200

def process_alerts(alert):
    alerts = alert.get('alerts', [])
    
    for a in alerts:
        status = a.get('status')
        labels = a.get('labels', {})
        annotations = a.get('annotations', {})
        summary = annotations.get('summary', 'No summary')
        description = annotations.get('description', '')
        
        # Get instance information
        instance = labels.get('instance', 'unknown')
        
        # Get attack type and normalize it
        attack_type = labels.get('attack_type', 'unknown')
        attack_subtype = labels.get('subtype', 'unknown') if attack_type == 'network_scan' else 'unknown'
        
        # Get IP address with fallbacks
        ip_addr = labels.get('client_ip_address', '0.0.0.0')
        if ip_addr == "0.0.0.0":
            ip_addr = labels.get('client_ip', '0.0.0.0')
            if "ffff" in ip_addr:
                ip_addr = ip_addr.split(":")[3]

        if "ffff" in ip_addr:
            ip_addr = ip_addr.split(":")[3]

        if instance != 'unknown':
            # Extract service name from instance (e.g., 'dotnet-ws1:8080' -> 'dotnet-ws1')
            service_name = instance.split(':')[0]
            
            # Create log entry
            log_entry = (
                f"Alertmanager Alert - "
                f"Status: {status}, "
                f"Service: {service_name}, "
                f"AttackType: {attack_type}, "
                f"SourceIp: {ip_addr}, "
                f"SubType: {attack_subtype}, "
                f"Summary: {summary}, "
                f"Description: {description}, "
                f"Labels: {labels}"
            )

            # Log to service-specific file if it's one of our services
            if service_name in service_loggers:
                service_loggers[service_name].info(log_entry)
                print(f"Logged alert for {service_name}")  # Debug logging
            else:
                print(f"Unknown service: {service_name}")  # Debug logging
            
            # Also log to main log file
            main_logger.info(log_entry)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
