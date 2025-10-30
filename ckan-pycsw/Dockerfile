FROM python:3.11.5-slim-bullseye
LABEL maintainer="96422458+mjanez@users.noreply.github.com"
LABEL org.opencontainers.image.source=https://github.com/mjanez/ckan-pycsw
LABEL org.opencontainers.image.description="ckan-pycsw base container image"
LABEL org.opencontainers.image.licenses=Unlicense

# Production non-root user
ENV USERNAME=ckan-pycsw
ENV USER_UID=10001
ENV USER_GID=$USER_UID

# ckan-pycsw envvars
ENV CKAN_PYCSW_VERSION=1.0.0
ENV APP_DIR=/srv/app
ENV TZ=UTC
RUN echo ${TZ} > /etc/timezone
ENV PYCSW_CKAN_SCHEMA=iso19139_inspire
ENV PYCSW_CONFIG=${APP_DIR}/pycsw.conf
ENV CKAN_URL=http://localhost:5000/
ENV PYCSW_PORT=8000
ENV PYCSW_URL=http://localhost:${PYCSW_PORT}/
ENV DEV_MODE=False
ENV TIMEOUT=300
ENV PYCSW_CRON_DAYS_INTERVAL=2
ENV PYCSW_CRON_HOUR_START=4
ENV SSL_UNVERIFIED_MODE=False

# PYCSW Catalog configuration
ENV CSW_IDENTIFICATION_TITLE="Sample Geospatial Catalogue" \
    CSW_IDENTIFICATION_ABSTRACT="OGC CSW server powered by pycsw" \
    CSW_PROVIDER_NAME="ckan-docker development team" \
    CSW_PROVIDER_URL="https://github.com/mjanez/ckan-docker" \
    CSW_CONTACT_NAME="ckan-docker development team" \
    CKAN_SYSADMIN_EMAIL="ckan.docker@example.org" \
    CSW_CONTACT_POSITION="Site Administrator" \
    CSW_CONTACT_ADDRESS==${CSW_CONTACT_NAME} \
    CSW_CONTACT_CITY="Madrid" \
    CSW_CONTACT_STATE_OR_PROVINCE="Madrid" \
    CSW_CONTACT_POSTAL_CODE="28001" \
    CSW_CONTACT_COUNTRY="Spain" \
    CSW_CONTACT_EMAIL=${CKAN_SYSADMIN_EMAIL} \
    CSW_CONTACT_URL=${CKAN_URL} \
    CSW_INSPIRE_DATE="2024-01-01" \
    CSW_INSPIRE_GEMET_KEYWORDS="Utility and governmental services" \
    CSW_INSPIRE_CONFORMITY="notEvaluated" \
    CSW_INSPIRE_CONTACT_NAME=${CSW_CONTACT_NAME} \
    CSW_INSPIRE_CONTACT_EMAIL=${CKAN_SYSADMIN_EMAIL} \
    CSW_INSPIRE_TEMP_EXTENT="2024-01-01/2024-12-31"

WORKDIR ${APP_DIR}

# Create a new non-root user and group, install necessary packages and remove the package list cache
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && chown -R $USERNAME:$USERNAME $APP_DIR \
    && apt-get -q -y update \
    && apt-get install -y --no-install-recommends \
        wget=1.21-1+deb11u1 \
        gettext-base=0.21-4 \
        curl \
    # Remove wait-for
    # wget --progress=dot:mega -O /wait-for https://raw.githubusercontent.com/eficode/wait-for/v2.2.4/wait-for \
    # && chmod +x /wait-for \
    && python3 -m pip install --no-cache-dir pdm==2.15.3 \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies with pdm
COPY pyproject.toml pdm.lock ./
RUN pdm install --no-self

# Update files
COPY ckan-pycsw/conf/pycsw.conf.template ckan-pycsw/docker-entrypoint.d/entrypoint.sh ./
COPY ckan2pycsw ckan2pycsw

ENTRYPOINT ["/bin/bash", "./entrypoint.sh"]
CMD ["tail", "-f", "/dev/null"]