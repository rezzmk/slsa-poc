#!/bin/bash
# token-refresh.sh

TOKEN_FILE="/tmp/wazuh_token"
WEBHOOK_URL="http://alert-webhook:9093/auth"

while true; do
    # Fetch new token
    TOKEN=$(curl -s $WEBHOOK_URL | jq -r '.token')
    
    if [ "$TOKEN" != "null" ] && [ ! -z "$TOKEN" ]; then
        echo "$TOKEN" > "$TOKEN_FILE"
        echo "Token updated successfully"
    else
        echo "Failed to get token"
    fi
    
    # Sleep for 55 minutes (tokens usually expire after 1 hour)
    sleep 3300
done
