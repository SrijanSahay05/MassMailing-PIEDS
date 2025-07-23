#!/bin/bash

DOMAIN="crm.srijansahay05.in"
EMAIL="your-email@example.com"  # <-- Change to your real email

set -e

# Stop anything using ports 80/443
sudo fuser -k 80/tcp || true
sudo fuser -k 443/tcp || true

echo "Stopping nginx docker container if running..."
docker-compose down || true

echo "Requesting SSL certificate for $DOMAIN using certbot..."
sudo certbot certonly --standalone --non-interactive --agree-tos --preferred-challenges http -d $DOMAIN -m $EMAIL

if [ ! -f /etc/letsencrypt/live/$DOMAIN/fullchain.pem ]; then
    echo "Certificate not found! Certbot may have failed."
    exit 1
fi

echo "Copying certificates to project directory for Docker..."
mkdir -p ./certs
sudo cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem ./certs/
sudo cp /etc/letsencrypt/live/$DOMAIN/privkey.pem ./certs/
sudo chown $(id -u):$(id -g) ./certs/fullchain.pem ./certs/privkey.pem

echo "Restarting nginx with SSL enabled..."
docker-compose up -d nginx

echo "SSL setup complete! Nginx should now serve HTTPS for $DOMAIN." 