# Stage 1: Build Fortran-Anwendung mit Makefile
FROM debian:bookworm-slim AS fortran-builder

# Labels für Build-Stage
LABEL stage="builder"
LABEL component="fortran-calculator"

# Build-Dependencies installieren
RUN apt-get update && apt-get install -y \
    gfortran \
    make \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Arbeitsverzeichnis erstellen
WORKDIR /build

# Fortran-Quellcode und Makefile kopieren
COPY src/*.f90 ./src/
COPY Makefile ./

# Fortran-Code mit Makefile kompilieren
RUN make

# Stage 2: Python-Anwendung mit Poetry vorbereiten
FROM python:3.12-slim AS python-builder

# Labels für Build-Stage
LABEL stage="builder"
LABEL component="python-api"

# Poetry installieren
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=false \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_CACHE_DIR=/tmp/poetry_cache \
    VIRTUAL_ENV=/opt/venv \
    PIP_ROOT_USER_ACTION=ignore

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       libxml2-dev libxslt1-dev python3-dev libxmlsec1-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*


# Arbeitsverzeichnis erstellen
WORKDIR /build

# Kopiere poetry.lock und pyproject.toml
COPY pyproject.toml poetry.lock* ./
COPY python/ ./python/
COPY gunicorn.conf.py README.md ./

# Dependencies direkt mit Poetry installieren (inklusive Gunicorn)
RUN pip install --upgrade pip \
    && python -m venv $VIRTUAL_ENV \
    && pip install poetry \
    && poetry config virtualenvs.create false \
    && poetry install --only main --no-interaction --no-ansi \
    && pip install gunicorn

# Stage 3: Runtime-Image erstellen
FROM python:3.12-slim

# OCI Labels gemäß Best Practices
LABEL org.opencontainers.image.title="Calculator Service" \
 org.opencontainers.image.description="Calculator service with Fortran backend and Python API" \
 org.opencontainers.image.vendor="Kaiserpfalz EDV-Service" \
 org.opencontainers.image.version="1.0.0" \
 org.opencontainers.image.created="2025-05-29" \
 org.opencontainers.image.authors="klenkes74 <rlichti@kaiserpfalz-edv.de>" \
 org.opencontainers.image.url="https://github.com/klenkes74/calculator-service" \
 org.opencontainers.image.source="https://github.com/klenkes74/calculator-service" \
 org.opencontainers.image.licenses="Apache-2.0"

# Environment-Variablen für Feature Toggles und Konfiguration
ENV PORT=8080 \
    WORKERS=4 \
    PYTHONUNBUFFERED=1 \
    FEATURE_METRICS_ENABLED=true \
    PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus \
    FEATURE_TRACING_ENABLED=false \
    FORTRAN_CALC_PATH=/app/bin/calculator \
    LOG_LEVEL=INFO \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH=/app \
    PIP_ROOT_USER_ACTION=ignore

# Arbeitsverzeichnis erstellen
WORKDIR /app


# Nicht-Root-Benutzer erstellen
RUN useradd -u 1000 -s /bin/false appuser \
    && chown -R appuser:appuser /app \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
       libgfortran5 libxml2-dev libxslt1-dev python3-dev libxmlsec1-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*


# Fortran-Binary aus dem Builder kopieren
COPY --from=fortran-builder /build/bin/calculator /app/bin/calculator

# Python-Anwendung aus dem Python-Builder kopieren
COPY --from=python-builder $VIRTUAL_ENV $VIRTUAL_ENV
COPY --from=python-builder /build/python /app/python
COPY --from=python-builder /build/gunicorn.conf.py /app/gunicorn.conf.py

# Logs-Verzeichnis erstellen
RUN mkdir -p /app/logs /tmp/prometheus \
    && chown -R appuser:appuser /app/logs /tmp/prometheus


# Port freigeben
EXPOSE 8080

# Auf Benutzer mit UID 1000 wechseln
USER 1000

# Starte Gunicorn mit vollqualifiziertem Pfad zur Konfiguration
CMD ["gunicorn", "--config", "gunicorn.conf.py", "--chdir", "/app", "python.wsgi:app"]