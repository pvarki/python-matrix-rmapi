#!/bin/bash -l
set -e
# Resolve our magic names to docker internal ip
GW_IP=$(getent ahostsv4 host.docker.internal | grep RAW | awk '{ print $1 }')
echo "GW_IP=$GW_IP"
grep -v -F -e "localmaeher"  -- /etc/hosts >/etc/hosts.new && cat /etc/hosts.new >/etc/hosts
echo "$GW_IP localmaeher.dev.pvarki.fi mtls.localmaeher.dev.pvarki.fi" >>/etc/hosts
echo "*** BEGIN /etc/hosts ***"
cat /etc/hosts
echo "*** END /etc/hosts ***"

if [ -f /data/persistent/public/mtlsclient.pem ]; then
  echo "Certificates exist, skipping init."
else
  /kw_product_init init /pvarki/kraftwerk-init.json
fi

if [ -f /data/persistent/firstrun.done ]
then
  echo "First run already cone"
else
  # FIXME: This should be done natively in the FastAPI app
  /kw_product_init ready --productname "matrix" --apiurl "https://api.example.com:8443/"  --userurl "https://example.com/"  /pvarki/kraftwerk-init.json
  date -u +"%Y%m%dT%H%M" >/data/persistent/firstrun.done
fi
