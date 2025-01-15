#!/bin/bash

LOCAL=`dirname $0`;
cd $LOCAL
cd ../

PWD=`pwd`
SCRIPT="notify-incident.sh"
ACTION=$1
USER=$2
IP=$3

# Optional parameters
ALERT_ID=$4
RULE_ID=$5

# Log locations
LOG_FILE="/var/ossec/logs/active-responses.log"

write_log() {
    echo "$(date) $1" >> ${LOG_FILE}
}

# Function to categorize the alert based on rule ID
get_alert_category() {
    case ${RULE_ID} in
        200001|200002|200003|200004) # DDoS rules
            echo "DDoS Attack"
            ;;
        200100|200101|200102|200103|200104|200105) # APT rules
            echo "APT Activity"
            ;;
        200200|200201|200202|200203|200204|200205) # Network Scanning rules
            echo "Network Scanning"
            ;;
        *)
            echo "Unknown Attack"
            ;;
    esac
}

# Send notification
send_notification() {
    CATEGORY=$(get_alert_category)
    MESSAGE="Security Incident: ${CATEGORY}\nIP: ${IP}\nRule ID: ${RULE_ID}\nAlert ID: ${ALERT_ID}"
    
    # Log the notification
    write_log "Security notification sent: ${MESSAGE}"
    
    # Here you could integrate with external notification systems
    # For example, sending to a webhook, email, or Slack
}

case ${ACTION} in
    add)
        send_notification
        ;;
    delete)
        # No action needed for delete
        ;;
    *)
        write_log "Invalid action: ${ACTION}"
        ;;
esac

exit 0;
