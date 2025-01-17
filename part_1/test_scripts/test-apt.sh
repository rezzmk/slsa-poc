#!/bin/bash
# APT Attack Demonstration Script

echo "Stage 1: Reconnaissance"
# Try multiple failed auth attempts
for i in {1..10}; do
    curl -X POST http://localhost:8081/api/admin
    sleep 2
done

echo -e "\nStage 2: Data Exfiltration Attempt"
# Request large amounts of data
for i in {1..5}; do
    curl "http://localhost:8081/api/data?size=1048576"
    sleep 1
done

echo -e "\nStage 3: C2 Beaconing Simulation"
# Simulate C2 beaconing with regular small requests
for i in {1..20}; do
    curl -X POST http://localhost:8081/api/beacon -d "{\"data\":\"beacon-$i\"}"
    sleep 30  # Regular interval typical of C2
done
