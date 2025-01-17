#!/usr/bin/env bash

# Enable debug mode
set -x

# Log locations
LOG_FILE="/var/ossec/logs/active-responses.log"
DEBUG_LOG="/var/ossec/logs/debug.log"

# Log function
write_log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') $1" | tee -a ${LOG_FILE} ${DEBUG_LOG}
}

write_log "Started block-attacker.sh with args: $@"

# Parse command
COMMAND=$1
ACTION="add"

# If command contains "delete" or ends in "delete", set action to delete
if [[ "$COMMAND" == *"delete"* ]]; then
    ACTION="delete"
fi

USER=$2
IP=$3
ALERT_ID=$4
RULE_ID=$5

write_log "Parsed arguments:"
write_log "COMMAND: $COMMAND"
write_log "ACTION: $ACTION"
write_log "USER: $USER"
write_log "IP: $IP"
write_log "ALERT_ID: $ALERT_ID"
write_log "RULE_ID: $RULE_ID"

# Check if iptables exists
if ! command -v iptables >/dev/null 2>&1; then
    write_log "ERROR: iptables not found"
    exit 1
fi

# Add IP to custom block list
add_block() {
    write_log "Attempting to block IP ${IP}"
    
    # Check if rule already exists
    if iptables -C INPUT -s ${IP} -j DROP 2>/dev/null; then
        write_log "Rule already exists for IP ${IP}"
        return 0
    fi

    # Try to add the rule
    if iptables -I INPUT -s ${IP} -j DROP; then
        write_log "Successfully added rule for IP ${IP}"
        # Log current rules
        write_log "Current iptables rules:"
        iptables -L -n | while read line; do write_log "$line"; done
        return 0
    else
        write_log "Failed to add rule for IP ${IP}"
        return 1
    fi
}

# Remove IP from block list
remove_block() {
    write_log "Attempting to remove block for IP ${IP}"
    
    if iptables -D INPUT -s ${IP} -j DROP 2>/dev/null; then
        write_log "Successfully removed block for IP ${IP}"
        return 0
    else
        write_log "No existing rule found for IP ${IP}"
        return 1
    fi
}

case ${ACTION} in
    add)
        write_log "Executing add action"
        add_block
        ;;
    delete)
        write_log "Executing delete action"
        remove_block
        ;;
    *)
        write_log "Invalid action: ${ACTION} from command ${COMMAND}"
        ;;
esac

write_log "Script completed"
