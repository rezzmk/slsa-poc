#!/bin/bash
# generate-certs.sh

mkdir -p ./config/nginx/ssl

# Generate self-signed certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout ./config/nginx/ssl/server.key \
    -out ./config/nginx/ssl/server.crt \
    -subj "/C=PT/ST=Aveiro/L=Aveiro/O=UA/CN=localhost"

# Set correct permissions
chmod 644 ./config/nginx/ssl/server.crt
chmod 644 ./config/nginx/ssl/server.key
