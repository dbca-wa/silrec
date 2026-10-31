#
# docker build --no-cache -t silrec-test .
# docker run --rm -it -p 8080:8080 -e ENABLE_WEB=True silrec-test /bin/bash
# Inside container:
# time python -c "import django"
# python -X importtime manage.py shell -c ""
#
# Prepare the base environment.
FROM ubuntu:24.04 AS builder_base_silrec

LABEL maintainer="asi@dbca.wa.gov.au"
LABEL org.opencontainers.image.source="https://github.com/dbca-wa/silrec"

ENV DEBIAN_FRONTEND=noninteractive
ENV DEBUG=True
ENV TZ=Australia/Perth
ENV EMAIL_HOST="smtp.corporateict.domain"
ENV DEFAULT_FROM_EMAIL='no-reply@dbca.wa.gov.au'
ENV NOTIFICATION_EMAIL='jawaid.mushtaq@dbca.wa.gov.au'
ENV NON_PROD_EMAIL='jawaid.mushtaq@dbca.wa.gov.au'
ENV PRODUCTION_EMAIL=False
ENV EMAIL_INSTANCE='DEV'
ENV SECRET_KEY="<ThisisNotRealKey>"
ENV SITE_PREFIX='silrec-dev'
ENV SITE_DOMAIN='dbca.wa.gov.au'
ENV OSCAR_SHOP_NAME='Forest Management Branch'
ENV BPAY_ALLOWED=False
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

# CVE-2026-111497 (Node2Shell): install patched Brotli (libbrotli1 >= 1.1.0-2ubuntu0.1)
# from noble-security/noble-updates. Node.js/npm are NOT installed in this stage any
# more - the frontend is built in the separate patched-Node stage below.
RUN apt-get clean && \
    apt-get update && \
    apt-get upgrade -y && \
    apt-get install --no-install-recommends -y \
        wget git libmagic-dev gcc binutils libproj-dev \
        build-essential python3 python3-setuptools python3-dev \
        python3-pip tzdata libreoffice cron rsyslog \
        libpq-dev patch postgresql-client mtr sqlite3 vim \
        ssh htop graphviz libgraphviz-dev pkg-config \
        run-one virtualenv software-properties-common \
        libbrotli1 libbrotli-dev python3-tk zip unzip && \
    # Install GDAL
    add-apt-repository ppa:ubuntugis/ubuntugis-unstable && \
    apt update && \
    apt-get install --no-install-recommends -y gdal-bin libgdal-dev python3-gdal && \
    # Ensure the patched Brotli decoder is present (CVE-2026-111497)
    apt-get install --no-install-recommends -y --only-upgrade libbrotli1 libbrotli-dev && \
    # Clean up
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Create user and directories
RUN groupadd -g 5000 oim && \
    useradd -g 5000 -u 5000 oim -s /bin/bash -d /app && \
    mkdir /app && \
    chown -R oim.oim /app

# Timezone setup
COPY timezone /etc/timezone
ENV TZ=Australia/Perth
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Copy and setup scripts
COPY startup.sh /
RUN chmod 755 /startup.sh

# Download utility scripts
RUN wget https://raw.githubusercontent.com/dbca-wa/wagov_utils/main/wagov_utils/bin/health_check.sh -O /bin/health_check.sh && \
    wget https://raw.githubusercontent.com/dbca-wa/wagov_utils/main/wagov_utils/bin-python/scheduler/scheduler.py -O /bin/scheduler.py && \
    chmod 755 /bin/health_check.sh /bin/scheduler.py

# --- Frontend build stage: patched Node.js (22.23.4 fixes CVE-2026-111497) ---
FROM node:22.23.4 AS frontend_builder
WORKDIR /app/silrec/frontend/silrec
COPY silrec/frontend/silrec/package.json silrec/frontend/silrec/package-lock.json ./
RUN npm ci --omit=dev
COPY silrec/frontend/silrec/ ./
# Static assets referenced by the frontend build (e.g. silrec/static/silrec/css/*)
COPY silrec/static/ /app/silrec/static/
RUN npm run build

FROM builder_base_silrec AS python_libs_silrec

WORKDIR /app
USER oim

# Create virtualenv and install requirements
RUN virtualenv /app/venv
ENV PATH=/app/venv/bin:$PATH
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=0

# Copy only requirements first for better caching
COPY --chown=oim:oim requirements.txt ./
RUN pip3 install --upgrade pip && \
    pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=oim:oim gunicorn.ini manage.py ./
COPY --chown=oim:oim python-cron python-cron
COPY --chown=oim:oim silrec ./silrec

# Copy pre-built frontend from the patched-Node build stage
COPY --from=frontend_builder --chown=oim:oim /app/silrec/static/silrec_vue ./silrec/static/silrec_vue

# Collect static files
RUN touch /app/.env && \
    python manage.py collectstatic --noinput

EXPOSE 8080
HEALTHCHECK --interval=1m --timeout=5s --start-period=10s --retries=3 CMD ["wget", "-q", "-O", "-", "http://localhost:8080/"]
CMD ["/startup.sh"]
