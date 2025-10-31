#!/bin/bash

set -xeuo pipefail

# Generate pycsw 3.0 YAML configuration from template
# PYCSW_CONFIG should be set to pycsw.yml (not pycsw.conf for pycsw 3.0)
envsubst < pycsw.yml.template > "${PYCSW_CONFIG:-pycsw.yml}"

# TODO: -Xfrozen_modules=off from: https://bugs.python.org/issue1666807

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

# Run database migration for pycsw 3.0
echo 'Running pycsw 3.0 database migration...'
bash docker-entrypoint.d/migrate_db_pycsw3.sh

# Ejecutar el comando Python
pdm run python3 -Xfrozen_modules=off ckan2pycsw/ckan2pycsw.py

exec "$@"
