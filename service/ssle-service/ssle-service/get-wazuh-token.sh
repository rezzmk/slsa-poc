#!/bin/bash

# Function to get API token
get_api_token() {
    local response
    response=$(curl -k -X POST "https://wazuh.manager:55000/security/user/authenticate" \
      -H "Authorization: Basic $(echo -n "${WAZUH_API_USER}:${WAZUH_API_PASSWORD}" | base64)" \
      -d '')
    
    echo "$response" | grep -o '"token":"[^"]*' | cut -d'"' -f4
}

# Get and export token
export WAZUH_API_TOKEN=$(get_api_token)
