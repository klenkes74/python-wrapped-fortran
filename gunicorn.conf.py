import os
import time
import sys
from datetime import datetime
from python.logging_config import setup_logger, extract_trace_context

# Basis-Einstellungen für Gunicorn
bind = "0.0.0.0:8080"
workers = int(os.environ.get("WORKERS", "4"))
threads = 2
timeout = 120
worker_class = "sync"

# Optional: Umgebungsvariablen für Feature Toggles setzen
os.environ.setdefault('ENABLE_PROMETHEUS', 'True')
os.environ.setdefault('ENABLE_OPENTELEMETRY', 'False')
os.environ.setdefault('PROMETHEUS_MULTIPROC_DIR', '/tmp/prometheus')

# Logging-Konfiguration einrichten
setup_logger()

# Access-Log-Format auf stdout ausgeben
accesslog = None
errorlog = None

# Loglevel für Gunicorn aus Umgebungsvariable übernehmen
loglevel = os.environ.get('LOG_LEVEL', 'info').lower()

# Prometheus-Verzeichnis bereinigen
multiprocess_dir = os.environ.get('PROMETHEUS_MULTIPROC_DIR', '/tmp/prometheus')
if os.path.exists(multiprocess_dir):
    for f in os.listdir(multiprocess_dir):
        os.unlink(os.path.join(multiprocess_dir, f))
else:
    os.makedirs(multiprocess_dir, exist_ok=True)

# Log-Handler für Worker-Prozesse beim Start konfigurieren
def post_fork(server, worker):
    # Hier können Worker-spezifische Log-Konfigurationen vorgenommen werden
    pass

def on_starting(server):
    # Logging vorbereiten, bevor Gunicorn vollständig startet
    pass