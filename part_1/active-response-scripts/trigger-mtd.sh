#!/bin/bash

LOCAL=`dirname $0`;
cd $LOCAL
cd ../

PWD=`pwd`
SCRIPT="trigger-mtd.sh"
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

# Trigger MTD rotation
trigger_rotation() {
    # Call the MTD service to rotate ports
    RESPONSE=$(curl -s -X POST http://mtd-service:8000/rotate)
    if [ $? -eq 0 ]; then
        write_log "Triggered MTD rotation due to attack from ${IP}. Response: ${RESPONSE}"
    else
        write_log "Failed to trigger MTD rotation for attack from ${IP}"
    fi
}

case ${ACTION} in
    add)
        trigger_rotation
        ;;
    delete)
        # No action needed for delete
        ;;
    *)
        write_log "Invalid action: ${ACTION}"
        ;;
esac

exit 0;
