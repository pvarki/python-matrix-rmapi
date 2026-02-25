#!/bin/bash -l
set -e
# Resolve our magic names to docker internal ip
GW_IP=$(getent ahostsv4 host.docker.internal | grep RAW | awk '{ print $1 }')
echo "GW_IP=$GW_IP"
grep -v -F -e "localmaeher"  -- /etc/hosts >/etc/hosts.new && cat /etc/hosts.new >/etc/hosts
echo "$GW_IP localmaeher.dev.pvarki.fi mtls.localmaeher.dev.pvarki.fi kc.localmaeher.dev.pvarki.fi" >>/etc/hosts
echo "*** BEGIN /etc/hosts ***"
cat /etc/hosts
echo "*** END /etc/hosts ***"

if [ -f /data/persistent/public/mtlsclient.pem ]; then
  echo "Certificates exist, skipping init."
else
  /kw_product_init init /pvarki/kraftwerk-init.json
  sleep 2
fi


# Generate the manifest using environment variables
# TODO use envsubst + dedicated file
cat <<EOF > /tmp/manifest.json
{
  "rasenmaeher": {
    "mtls": {
      "base_uri": "${MTLS_DOMAIN}"
    },
    "kc": {
      "base_uri": "${KCDOMAIN}",
      "realm": "${KCREALM}"
    }
  },
  "oidc": {
    "client_registration": {
      "client_name": "Synapse",
    }
  }
}
EOF

MAX_RETRIES=5
COUNT=0
until /kc_client_init get_jwt /tmp/manifest.json || [ $COUNT -eq $MAX_RETRIES ]; do
  echo "JWT fetch failed, retrying in 2s..."
  sleep 2
  ((COUNT++))
done

# Register the synapse server as an OIDC integration
/kc_client_init register_oidc /tmp/manifest.json

if [ -f /data/persistent/firstrun.done ]
then
  echo "First run already cone"
else
  # FIXME: This should be done natively in the FastAPI app
  # /kw_product_init ready --productname "matrix" --apiurl "https://api.example.com:8443/"  --userurl "https://example.com/"  /pvarki/kraftwerk-init.json
  date -u +"%Y%m%dT%H%M" >/data/persistent/firstrun.done
fi
