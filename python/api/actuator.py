# python/api/routes.py

from flask import jsonify, Flask, request
import prometheus_client
from prometheus_client import multiprocess, CONTENT_TYPE_LATEST
import subprocess
import os
import json
import time
from python.metrics import track_request_metrics, track_fortran_call, metrics_registry
from python.logging_config import setup_logger, extract_trace_context, default_logger

CALCULATOR_PATH = os.path.abspath("./bin/calculator")

# Logger für die API-Komponente einrichten
logger = setup_logger("calculator-api")

def register_actuator(app):
    @app.before_request
    def before_request():
        request.logger = default_logger
        request.start_time = time.time()
        request.logger.debug(f"Anfrage gestartet: {request.method} {request.path}")

    @app.after_request
    def after_request(response):
        request.logger.debug(f"Anfrage abgeschlossen: {request.method} {request.path} - Status: {response.status_code}")
        return response


    @app.route('/actuator')
    def actuator():
        return jsonify({
            "message": "Willkommen beim Calculator API",
            "endpoints": {
                "/actuator/health": "k8s health check",
                "/actuator/prometheus": "Prometheus-Metriken abrufen (wenn aktiviert)",
                "/actuator/debug": "Debug-Informationen der Anwendung abrufen"
                # end::[]"
            }
        })

    @app.route('/actuator/health')
    def health_check():
        trace_id, span_id, parent_span_id = extract_trace_context()

        # Log-Eintrag mit Trace-Kontext
        log_extra = {'trace_id': trace_id, 'span_id': span_id, 'parent_span_id': parent_span_id}
        logger.info("Gesundheitscheck durchgeführt", extra=log_extra)

        response = jsonify({
            "status": "healthy",
            "trace_id": trace_id,
            "span_id": span_id,
            "parent_span_id": parent_span_id
        })

        # Tracing-Header zur Antwort hinzufügen
        response.headers['traceparent'] = f'00-{trace_id}-{span_id}-01'
        response.headers['X-Trace-Id'] = trace_id
        response.headers['X-Span-Id'] = span_id
        response.headers['X-Parent-Span-Id'] = parent_span_id

        return response

    @app.route('/actuator/prometheus', methods=['GET'])
    def metrics():
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
        try:
            ENABLE_PROMETHEUS = os.environ.get('ENABLE_PROMETHEUS', True)
            if not ENABLE_PROMETHEUS:
                return jsonify({"error": "Prometheus-Metriken sind deaktiviert"}), 503

            output = generate_latest(metrics_registry)

        except Exception as e:
            return jsonify({"error": "Fehler beim Abrufen der Metriken: {str(e)}"}), 500

        return output, 200, {'Content-Type': CONTENT_TYPE_LATEST}

    @app.route('/actuator/debug', methods=['GET'])
    def debug():
        """
        Debug-Endpoint, um den aktuellen Zustand der Anwendung zu überprüfen
        """
        trace_id, span_id, parent_span_id = extract_trace_context()
        logger.info("Debug-Informationen abgerufen", extra={'trace_id': trace_id, 'span_id': span_id, 'parent_span_id': parent_span_id})

        debug_info = {
            "trace_id": trace_id,
            "span_id": span_id,
            "parent_span_id": parent_span_id,
            "environment": dict(os.environ),
            "python_version": os.sys.version,
            "hostname": os.uname().nodename
        }

        return jsonify(debug_info)

    return app