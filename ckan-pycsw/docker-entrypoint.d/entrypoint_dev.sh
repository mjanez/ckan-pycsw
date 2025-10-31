#!/bin/bash

set -xeuo pipefail

# Generate pycsw 3.0 YAML configuration from template
# PYCSW_CONFIG should be set to pycsw.yml (not pycsw.conf for pycsw 3.0)
envsubst < pycsw.yml.template > "${PYCSW_CONFIG:-pycsw.yml}"

# Check if SSL_UNVERIFIED_MODE is enabled
if [ "${SSL_UNVERIFIED_MODE:-false}" = "true" ] || [ "${SSL_UNVERIFIED_MODE:-false}" = "True" ]; then
    export REQUESTS_CA_BUNDLE=""
    export CURL_CA_BUNDLE=""
    SSL_FLAGS="--insecure"  # Add SSL ignore flag
    echo "[INSECURE] SSL_UNVERIFIED_MODE is enabled. SSL certificate verification is disabled."
else
    SSL_FLAGS=""
fi

# Use curl directly instead of wait-for if necessary
echo 'Waiting for $CKAN_URL to become available...'
until curl $SSL_FLAGS --output /dev/null --silent --head --fail "$CKAN_URL"; do
    printf '.'
    sleep 5
done
echo 'CKAN is available.'

# Execute Python command with debugging (using debugpy instead of deprecated ptvsd)
python3 -m debugpy --listen 0.0.0.0:${PYCSW_DEV_PORT} --wait-for-client ckan2pycsw/ckan2pycsw.py

exec "$@"
