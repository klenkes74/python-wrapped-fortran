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

def register_routes(app):
    @app.before_request
    def before_request():
        request.logger = default_logger
        request.start_time = time.time()
        request.logger.debug(f"Anfrage gestartet: {request.method} {request.path}")

    @app.after_request
    def after_request(response):
        request.logger.debug(f"Anfrage abgeschlossen: {request.method} {request.path} - Status: {response.status_code}")
        return response


    @app.route('/')
    def index():
        return jsonify({
            "message": "Willkommen beim Calculator API",
            "endpoints": {
                "/add": "Addition zweier Zahlen (GET, Parameter: a, b)",
                "/sub": "Subtraktion zweier Zahlen (GET, Parameter: a, b)",
                "/mul": "Multiplikation zweier Zahlen (GET, Parameter: a, b)",
                "/div": "Division zweier Zahlen (GET, Parameter: a, b)",
                "/api/health": "k8s health check",
                "/metrics": "Prometheus-Metriken abrufen (wenn aktiviert)"

                # end::[]"
            }
        })

    @app.route('/api/health')
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

    def calculate(operation):
        """
        Generische Funktion für alle Rechenoperationen
        """
        trace_id, span_id, parent_span_id = extract_trace_context()

        # Log-Kontext für diese Anfrage
        log_extra = {'trace_id': trace_id, 'span_id': span_id, 'parent_span_id': parent_span_id}

        try:
            a = request.args.get('a', type=float)
            b = request.args.get('b', type=float)

            if a is None or b is None:
                logger.warning(f"Fehlende Parameter bei {operation}-Operation", extra=log_extra)
                response = jsonify({
                    "error": "Parameter 'a' und 'b' müssen als Zahlen angegeben werden",
                    "trace_id": trace_id,
                    "span_id": span_id,
                    "parent_span_id": parent_span_id
                }), 400
                if isinstance(response, tuple) and len(response) > 0:
                    response[0].headers['traceparent'] = f'00-{trace_id}-{span_id}-01'
                    response[0].headers['X-Trace-Id'] = trace_id
                    response[0].headers['X-Span-Id'] = span_id
                    response[0].headers['X-Parent-Span-Id'] = parent_span_id
                return response

            logger.info(f"{operation}-Operation gestartet mit a={a}, b={b}", extra=log_extra)

            # Umgebungsvariablen für das Fortran-Programm bereitstellen
            env = os.environ.copy()
            env['TRACE_ID'] = trace_id
            env['SPAN_ID'] = span_id
            env['PARENT_SPAN_ID'] = parent_span_id

            # Aufruf des Fortran-Programms mit der übergebenen Operation und Trace-Kontext
            result = subprocess.run(
                [CALCULATOR_PATH, str(a), str(b), operation],
                capture_output=True,
                text=True,
                env=env
            )

            if result.returncode != 0:
                error_msg = f"Fehler bei der Berechnung: {result.stderr}"
                logger.error(error_msg, extra=log_extra)
                response = jsonify({
                    "error": error_msg,
                    "trace_id": trace_id,
                    "span_id": span_id,
                    "parent_span_id": parent_span_id
                }), 500
                if isinstance(response, tuple) and len(response) > 0:
                    response[0].headers['traceparent'] = f'00-{trace_id}-{span_id}-01'
                    response[0].headers['X-Trace-Id'] = trace_id
                    response[0].headers['X-Span-Id'] = span_id
                    response[0].headers['X-Parent-Span-Id'] = parent_span_id
                return response

            # Ausgabe des Fortran-Programms parsen
            output = float(result.stdout.strip())

            logger.info(f"{operation}-Operation erfolgreich: {a} {operation} {b} = {output}", extra=log_extra)

            response = jsonify({
                "result": output,
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

        except Exception as e:
            error_msg = f"Unerwarteter Fehler bei {operation}: {str(e)}"
            logger.error(error_msg, exc_info=True, extra=log_extra)
            response = jsonify({
                "error": str(e),
                "trace_id": trace_id,
                "span_id": span_id
            }), 500
            if isinstance(response, tuple) and len(response) > 0:
                response[0].headers['traceparent'] = f'00-{trace_id}-{span_id}-01'
                response[0].headers['X-Trace-Id'] = trace_id
                response[0].headers['X-Span-Id'] = span_id
                response[0].headers['X-Parent-Span-Id'] = parent_span_id
            return response

    # Endpunkte für die verschiedenen Operationen
    @app.route('/add', methods=['GET'])
    @track_request_metrics
    def add():
        return calculate("add")

    @app.route('/sub', methods=['GET'])
    @track_request_metrics
    def subtract():
        return calculate("sub")

    @app.route('/mul', methods=['GET'])
    @track_request_metrics
    def multiply():
        return calculate("mul")

    @app.route('/div', methods=['GET'])
    @track_request_metrics
    def divide():
        return calculate("div")

    @app.route('/metrics', methods=['GET'])
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

    @app.route('/debug', methods=['GET'])
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