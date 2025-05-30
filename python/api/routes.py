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

                # end::[]"
            }
        })

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
                    if parent_span_id != 'unset':
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
                    if parent_span_id != 'unset':
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
            if parent_span_id != 'unset':
                response[0].headers['X-Parent-Span-Id'] = parent_span_id

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
                if parent_span_id != 'unset':
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

    return app