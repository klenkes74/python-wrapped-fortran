# Python-Wrapped Fortran

Dieses Projekt stellt einen WSGI-Webservice bereit, der ein Fortran-Programm als Microservice mit REST-Interface einpackt.

## Features

- Flask-basierter WSGI-Webserver
- JSON-strukturierte Logging
- Prometheus Metrics (optional aktivierbar)
- OpenTelemetry Integration (optional aktivierbar)
- Feature-Toggles für Observability-Komponenten

## Installation

Voraussetzungen:
- Python 3.11 oder höher
- Poetry

Installation der Abhängigkeiten:

```bash
poetry install
```

## Konfiguration

Die Anwendung lässt sich über Umgebungsvariablen konfigurieren:

| Variable | Beschreibung | Standard |
|----------|--------------|----------|
| `ENABLE_PROMETHEUS` | Aktiviert/deaktiviert Prometheus-Metriken | `True` |
| `ENABLE_OPENTELEMETRY` | Aktiviert/deaktiviert OpenTelemetry | `False` |
| `DEBUG` | Aktiviert/deaktiviert Debug-Modus | `False` |
| `FLASK_ENV` | Flask-Umgebung (`development`/`production`) | `production` |


## Logging

Die Anwendung verwendet JSON-strukturiertes Logging mit folgendem Format:

```json
{
  "timestamp": "2023-05-25T14:30:45.123456+00:00",
  "level": "INFO",
  "name": "python-wrapped-fortran",
  "message": "Server started"
}
```

## Starten der Anwendung

Die Anwendung kann mit folgendem Befehl gestartet werden:

```bash
poetry run gunicorn python.wsgi:app -c gunicorn.conf.py
```

Nach dem Start ist der Service unter `http://localhost:8080` verfügbar.

## Endpoints

- `/api/health` - Gesundheitsstatus der Anwendung
- `/metrics` - Prometheus Metriken (wenn aktiviert)

## Entwicklung

### Testen

```bash
poetry run pytest
```

### Code-Formatierung

```bash
poetry run black python tests
poetry run isort python tests
```

### Lint

```bash
poetry run flake8 python tests
```

## Lizenz

Apache License 2.0