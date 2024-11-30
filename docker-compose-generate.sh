#!/bin/bash

NUM_INSTANCES=${1:-3}

car << EOF > docker-compose.yml
name: SSLE-POC-114834

services:
  dotnet-ws-node-template: &dotnet-ws-node-template
    build: ./service/ssle-service/ssle-service/
    restart: always
    networks:
      - internal-poc-network
    volumes:
      - ./service/ssle-service/ssle-service/ossec.conf:/wazuh-config-mount/etc/ossec.conf
      - ./service/ssle-service/ssle-service/internal_options.conf:/wazuh-config-mount/etc/local_internal_options.conf
    environment:
      - SERVICE_NAME=dotnet-ws

EOF

for i in $(seq 1 $NUM_INSTANCES); do
cat << EOF >> docker-compose.yml

  dotnet-ws$i:
    <<: *dotnet-ws-node-template
    hostname: dotnet-ws$i
    ports:
      - "808$i:8080"
    volumes:
      - ws$i-logs:/app/logs
      - alertmanager_logs:/app/logs
    environment:
      - SERVICE_NAME=dotnet-ws$i

EOF
done

cat << EOF >> docker-compose.yml

  prometheus-webhook:
    hostname: prometheus-webhook
    build:
      context: ./prometheus-webhook
    container_name: prometheus-webhook
    ports:
      - "5001:5001"
    networks:
      - internal-poc-network
    volumes:
      - alertmanager_logs:/app/logs

  alertmanager:
    image: prom/alertmanager:latest
    container_name: alertmanager
    ports:
      - "9093:9093"
    volumes:
      - ./config/alertmanager/alertmanager.yml:/etc/alertmanager/alertmanager.yml
      - alertmanager_data:/alertmanager
      - alertmanager_logs:/app/logs
    networks:
      - internal-poc-network

  wazuh.manager:
    container_name: wmanager
    image: wazuh/wazuh-manager:4.9.2
    hostname: wazuh.manager
    restart: always
    ulimits:
      memlock:
        soft: -1
        hard: -1
      nofile:
        soft: 655360
        hard: 655360
    ports:
      - "1514:1514"
      - "1515:1515"
      - "514:514/udp"
      - "55000:55000"
      - "9101:9100"
    environment:
      - INDEXER_URL=https://wazuh.indexer:9200
      - INDEXER_USERNAME=admin
      - INDEXER_PASSWORD=SecretPassword
      - FILEBEAT_SSL_VERIFICATION_MODE=full
      - SSL_CERTIFICATE_AUTHORITIES=/etc/ssl/root-ca.pem
      - SSL_CERTIFICATE=/etc/ssl/filebeat.pem
      - SSL_KEY=/etc/ssl/filebeat.key
      - API_USERNAME=wazuh-wui
      - API_PASSWORD=MyS3cr37P450r.*-
    volumes:
      - wazuh_api_configuration:/var/ossec/api/configuration
      - wazuh_etc:/var/ossec/etc
      - wazuh_logs:/var/ossec/logs
      - wazuh_queue:/var/ossec/queue
      - wazuh_var_multigroups:/var/ossec/var/multigroups
      - wazuh_integrations:/var/ossec/integrations
      - wazuh_active_response:/var/ossec/active-response/bin
      - wazuh_agentless:/var/ossec/agentless
      - wazuh_wodles:/var/ossec/wodles
      - filebeat_etc:/etc/filebeat
      - filebeat_var:/var/lib/filebeat
      - ./config/prometheus:/etc/prometheus:ro
      - ./config/wazuh_indexer_ssl_certs/root-ca-manager.pem:/etc/ssl/root-ca.pem
      - ./config/wazuh_indexer_ssl_certs/wazuh.manager.pem:/etc/ssl/filebeat.pem
      - ./config/wazuh_indexer_ssl_certs/wazuh.manager-key.pem:/etc/ssl/filebeat.key
      - ./config/wazuh_cluster/wazuh_manager.conf:/wazuh-config-mount/etc/ossec.conf
      - ./config/wazuh_cluster/local_decoder.xml:/wazuh-config-mount/etc/decoders/local_decoder.xml
      - ./config/wazuh_cluster/local_rules.xml:/wazuh-config-mount/etc/rules/local_rules.xml
    networks:
      - internal-poc-network

  wazuh.indexer:
    container_name: windexer
    image: wazuh/wazuh-indexer:4.9.2
    hostname: wazuh.indexer
    restart: always
    ports:
      - "9200:9200"
    environment:
      - "OPENSEARCH_JAVA_OPTS=-Xms1g -Xmx1g"
    ulimits:
      memlock:
        soft: -1
        hard: -1
      nofile:
        soft: 65536
        hard: 65536
    volumes:
      - wazuh-indexer-data:/var/lib/wazuh-indexer
      - ./config/wazuh_indexer_ssl_certs/root-ca.pem:/usr/share/wazuh-indexer/certs/root-ca.pem
      - ./config/wazuh_indexer_ssl_certs/wazuh.indexer-key.pem:/usr/share/wazuh-indexer/certs/wazuh.indexer.key
      - ./config/wazuh_indexer_ssl_certs/wazuh.indexer.pem:/usr/share/wazuh-indexer/certs/wazuh.indexer.pem
      - ./config/wazuh_indexer_ssl_certs/admin.pem:/usr/share/wazuh-indexer/certs/admin.pem
      - ./config/wazuh_indexer_ssl_certs/admin-key.pem:/usr/share/wazuh-indexer/certs/admin-key.pem
      - ./config/wazuh_indexer/wazuh.indexer.yml:/usr/share/wazuh-indexer/opensearch.yml
      - ./config/wazuh_indexer/internal_users.yml:/usr/share/wazuh-indexer/opensearch-security/internal_users.yml
    networks:
      - internal-poc-network

  wazuh.dashboard:
    container_name: wdashboard
    image: wazuh/wazuh-dashboard:4.9.2
    hostname: wazuh.dashboard
    restart: always
    ports:
      - 444:5601
    environment:
      - INDEXER_USERNAME=admin
      - INDEXER_PASSWORD=SecretPassword
      - WAZUH_API_URL=https://wazuh.manager
      - DASHBOARD_USERNAME=kibanaserver
      - DASHBOARD_PASSWORD=kibanaserver
      - API_USERNAME=wazuh-wui
      - API_PASSWORD=MyS3cr37P450r.*-
    volumes:
      - ./config/wazuh_indexer_ssl_certs/wazuh.dashboard.pem:/usr/share/wazuh-dashboard/certs/wazuh-dashboard.pem
      - ./config/wazuh_indexer_ssl_certs/wazuh.dashboard-key.pem:/usr/share/wazuh-dashboard/certs/wazuh-dashboard-key.pem
      - ./config/wazuh_indexer_ssl_certs/root-ca.pem:/usr/share/wazuh-dashboard/certs/root-ca.pem
      - ./config/wazuh_dashboard/opensearch_dashboards.yml:/usr/share/wazuh-dashboard/config/opensearch_dashboards.yml
      - ./config/wazuh_dashboard/wazuh.yml:/usr/share/wazuh-dashboard/data/wazuh/config/wazuh.yml
      - wazuh-dashboard-config:/usr/share/wazuh-dashboard/data/wazuh/config
      - wazuh-dashboard-custom:/usr/share/wazuh-dashboard/plugins/wazuh/public/assets/custom
    depends_on:
      - wazuh.indexer
    links:
      - wazuh.indexer:wazuh.indexer
      - wazuh.manager:wazuh.manager
    networks:
      - internal-poc-network

  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./config/prometheus:/etc/prometheus:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/usr/share/prometheus/console_libraries'
      - '--web.console.templates=/usr/share/prometheus/consoles'
    depends_on:
      - wazuh.manager
      - node-exporter
    networks:
      - internal-poc-network

  node-exporter:
    image: prom/node-exporter:v1.3.1
    container_name: node-exporter
    ports:
      - "9102:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--collector.netstat'
      - '--path.procfs=/host/proc'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.ignored-mount-points=^/(sys|proc|dev|host|etc|mnt/host|run/desktop|parent-distro)($$|/)'
    networks:
      - internal-poc-network
    user: root
    privileged: true

volumes:
EOF

for i in $(seq 1 $NUM_INSTANCES); do
cat << EOF >> docker-compose.yml
  ws$i-logs:
    driver: local
EOF
done

cat << EOF >> docker-compose.yml
  wazuh_api_configuration:
  wazuh_etc:
  wazuh_logs:
  wazuh_queue:
  wazuh_var_multigroups:
  wazuh_integrations:
  wazuh_active_response:
  wazuh_agentless:
  wazuh_wodles:
  filebeat_etc:
  filebeat_var:
  wazuh-indexer-data:
  wazuh-dashboard-config:
  wazuh-dashboard-custom:
  prometheus_data:
  alertmanager_data:
  alertmanager_logs:

networks:
  internal-poc-network:
    driver: bridge
EOF
