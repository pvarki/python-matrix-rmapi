#!/bin/bash -l
set -e
# Resolve our magic names to docker internal ip
GW_IP=$(getent ahostsv4 host.docker.internal | grep RAW | awk '{ print $1 }')
echo "GW_IP=$GW_IP"
grep -v "$GW_IP" /etc/hosts > /etc/hosts.new && cat /etc/hosts.new > /etc/hosts
echo "$GW_IP ${SERVER_DOMAIN} ${MTLS_DOMAIN}" >>/etc/hosts
echo "*** BEGIN /etc/hosts ***"
cat /etc/hosts
echo "*** END /etc/hosts ***"


if [ -f /data/persistent/public/mtlsclient.pem ]; then
  echo "Certificates exist, skipping init."
else
  /kw_product_init init /pvarki/kraftwerk-init.json
  sleep 2
fi

if [ -f /data/persistent/firstrun.done ]
then
  echo "First run already cone"
else
  date -u +"%Y%m%dT%H%M" >/data/persistent/firstrun.done
fi
