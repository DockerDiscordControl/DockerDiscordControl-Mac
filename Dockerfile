# Multi-Stage Build - Alpine Version for DDC
FROM python:3.12-alpine AS builder
WORKDIR /build

# Install build dependencies with security updates and C++ compiler
RUN apk update && apk upgrade && \
    apk add --no-cache --virtual .build-deps gcc g++ musl-dev python3-dev libffi-dev make && \
    apk add --no-cache openssl=3.5.1-r0 openssl-dev=3.5.1-r0

# Copy requirements and install Python packages with latest setuptools
COPY requirements.txt .
RUN python -m venv /venv && \
    /venv/bin/pip install --no-cache-dir --upgrade pip setuptools && \
    /venv/bin/pip install --no-cache-dir -r requirements.txt && \
    /venv/bin/pip install --no-cache-dir --force-reinstall --upgrade "aiohttp>=3.12.14" "setuptools>=78.1.1" && \
    /venv/bin/pip install --no-cache-dir --force-reinstall --upgrade "setuptools>=78.1.1" && \
    /venv/bin/pip wheel --wheel-dir=/wheels -r requirements.txt

# Copy source code and compile (suppress git warnings)
COPY . /build/
RUN python -m compileall -b /build 2>/dev/null || python -m compileall -b /build

# Clean up build dependencies
RUN apk del .build-deps

# Final stage
FROM python:3.12-alpine
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/venv/bin:$PATH" \
    DOCKER_HOST="unix:///var/run/docker.sock"

# Install runtime dependencies with security updates
RUN apk update && apk upgrade && \
    apk add --no-cache supervisor curl ca-certificates docker-cli && \
    apk del openssl && \
    apk add --no-cache openssl=3.5.1-r0 && \
    ln -sf /usr/local/bin/python3 /usr/local/bin/python

# Copy from builder
COPY --from=builder /venv /venv
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir --no-index --find-links=/wheels /wheels/* && \
    pip install --no-cache-dir --force-reinstall --upgrade "aiohttp>=3.11.16" "setuptools>=78.1.1" && \
    pip install --no-cache-dir --force-reinstall --upgrade setuptools && \
    rm -rf /wheels

COPY --from=builder /build /app
RUN find /app -name "*.py" -not -path "*/app/*" -delete && \
    find /app -name "*.pyc" -not -path "*/app/*" -delete && \
    rm -rf /app/.git /app/.github /app/tests /app/venv

# Configure supervisor and directories
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
RUN mkdir -p /app/config /app/logs /app/app/logs /app/scripts /app/heartbeat_monitor && \
    chmod 777 /app/config /app/logs /app/app/logs

# Copy scripts and monitor
COPY scripts/fix_permissions.sh /app/scripts/
RUN chmod +x /app/scripts/fix_permissions.sh
COPY heartbeat_monitor/ddc_heartbeat_monitor.py /app/heartbeat_monitor/

EXPOSE 9374
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"] 