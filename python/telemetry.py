from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor

def configure_telemetry(app):
    if not app.config.get('ENABLE_OPENTELEMETRY', True):
        app.logger.info("OpenTelemetry disabled")
        return app

    app.logger.info("Configuring OpenTelemetry")

    # Tracer Provider konfigurieren
    trace.set_tracer_provider(TracerProvider())

    # Exporter konfigurieren (für Produktion OTLP-Exporter verwenden)
    span_processor = BatchSpanProcessor(ConsoleSpanExporter())
    trace.get_tracer_provider().add_span_processor(span_processor)

    # Flask instrumentieren
    FlaskInstrumentor().instrument_app(app)

    return app