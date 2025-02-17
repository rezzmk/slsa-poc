#!/bin/bash

# Enable error reporting
set -e

cat > /var/ossec/etc/ossec.conf << EOF
<ossec_config>
  <client>
    <server>
      <address>wazuh.manager</address>
      <port>1514</port>
    </server>
  </client>

  <command>
    <name>host-deny</name>
    <executable>host-deny</executable>
    <timeout_allowed>yes</timeout_allowed>
  </command>

  <client_buffer>
    <disabled>no</disabled>
    <queue_size>100000</queue_size>
    <events_per_second>1000</events_per_second>
  </client_buffer>

  <!-- Application logs -->
  <localfile>
    <log_format>syslog</log_format>
    <location>/app/logs/app*.log</location>
  </localfile>

  <!-- Service-specific alert monitoring -->
  <localfile>
    <log_format>syslog</log_format>
    <location>/app/logs/alertmanager_$SERVICE_NAME.log</location>
  </localfile>

  <logging>
    <log_level>debug</log_level>
  </logging>

  <wodle name="syscollector">
    <disabled>no</disabled>
    <interval>1h</interval>
    <scan_on_start>yes</scan_on_start>
    <hardware>yes</hardware>
    <os>yes</os>
    <network>yes</network>
    <packages>yes</packages>
    <ports all="no">yes</ports>
    <processes>yes</processes>

    <synchronization>
      <max_eps>10</max_eps>
    </synchronization>
  </wodle>
</ossec_config>
EOF

/var/ossec/bin/wazuh-control start

exec dotnet ssle-service.dll
