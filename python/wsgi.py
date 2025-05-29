from flask import Flask
from python.api.routes import register_routes
from python.logging_config import setup_logger, extract_trace_context
from python.telemetry import configure_telemetry
from python.metrics import configure_metrics

def create_app():
    app = Flask(__name__)

    # Konfiguration laden
    app.config.from_object('python.config.Config')

    # Logging konfigurieren
    setup_logger("calculator-app")

    # OpenTelemetry konfigurieren
    configure_telemetry(app)

    # Prometheus Metrics konfigurieren
    configure_metrics(app)

    # API-Routen registrieren
    register_routes(app)

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)