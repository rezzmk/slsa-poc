#!/bin/sh

LOCAL=`dirname $0`;
cd $LOCAL
cd ../

PWD=`pwd`
SCRIPT="block-attacker.sh"
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

# Add IP to custom block list
add_block() {
    /usr/sbin/iptables -I INPUT -s ${IP} -j DROP
    /usr/sbin/iptables -I FORWARD -s ${IP} -j DROP
    write_log "Blocked IP ${IP} for attack type: ${RULE_ID}"
}

# Remove IP from custom block list
remove_block() {
    /usr/sbin/iptables -D INPUT -s ${IP} -j DROP
    /usr/sbin/iptables -D FORWARD -s ${IP} -j DROP
    write_log "Removed block for IP ${IP}"
}

case ${ACTION} in
    add)
        add_block
        ;;
    delete)
        remove_block
        ;;
    *)
        write_log "Invalid action: ${ACTION}"
        ;;
esac

exit 0;
