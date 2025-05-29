# python/api/logging_config.py

import json
import logging
import datetime
import sys
import uuid
import re
import socket
import traceback
from flask import request

class SpringBootJsonFormatter(logging.Formatter):
    def format(self, record):
        # Spring Boot JSON Log Format
        timestamp = datetime.datetime.now().isoformat()

        # Grundlegende Log-Felder nach Spring Boot-Standard
        log_record = {
            "@timestamp": timestamp,
            "level": record.levelname,
            "thread_name": f"thread-{record.thread}",
            "logger_name": record.name,
            "message": record.getMessage(),
            "process": {
                "pid": record.process,
                "thread_id": record.thread
            },
            "host": {
                "name": socket.gethostname()
            },
            "service": {
                "name": "calculator-service"
            }
        }

        # Trace-Kontext
        if hasattr(record, 'trace_id'):
            log_record["traceId"] = record.trace_id
        if hasattr(record, 'span_id'):
            log_record["spanId"] = record.span_id

        # Exception-Details hinzufügen, falls vorhanden
        if record.exc_info:
            exc_type, exc_value, exc_tb = record.exc_info
            formatted_exception = traceback.format_exception(exc_type, exc_value, exc_tb)
            log_record["exception"] = {
                "class": exc_type.__name__,
                "message": str(exc_value),
                "stacktrace": "".join(formatted_exception)
            }

        # Zusätzliche Felder hinzufügen
        if hasattr(record, 'additional_fields'):
            for key, value in record.additional_fields.items():
                log_record[key] = value

        return json.dumps(log_record)

def setup_logger(logger_name="calculator-app"):
    """Richtet einen Logger mit Spring Boot JSON-Formatierung ein"""
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)

    # Bestehende Handler entfernen, um Duplikate zu vermeiden
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(SpringBootJsonFormatter())
    logger.addHandler(handler)

    return logger

def extract_trace_context():
    """Extrahiert Trace-Kontext aus eingehenden Headern oder erstellt neuen"""
    trace_id = None
    span_id = None
    parent_span_id = None
    logger = logging.getLogger("calculator-app")

    try:
        # Nur Ausführen, wenn es in einem Flask-Kontext ist
        if request:
            # 1. W3C Trace Context prüfen (traceparent)
            traceparent = request.headers.get('traceparent')
            if traceparent:
                # Format: 00-trace_id-span_id-flags
                match = re.match(r'00-([0-9a-f]{32})-([0-9a-f]{16})-[0-9a-f]{2}', traceparent)
                if match:
                    trace_id = match.group(1)
                    parent_span_id = match.group(2)
                    if not parent_span_id:
                        parent_span_id = 'unset'
                    span_id = str(uuid.uuid4()).replace('-', '')[:16]
                    logger.debug(f"Trace-Kontext aus W3C traceparent extrahiert",
                              extra={'trace_id': trace_id, 'span_id': span_id, 'parent_span_id': parent_span_id})

            # 2. Jaeger/OpenTracing-Header prüfen
            elif request.headers.get('uber-trace-id'):
                trace_header = request.headers.get('uber-trace-id')
                parts = trace_header.split(':')
                if len(parts) >= 2:
                    trace_id = parts[0]
                    parent_span_id = parts[1]
                    if not parent_span_id:
                        parent_span_id = 'unset'
                    span_id = str(uuid.uuid4()).replace('-', '')[:16]
                    logger.debug(f"Trace-Kontext aus Jaeger-Header extrahiert",
                              extra={'trace_id': trace_id, 'span_id': span_id, 'parent_span_id': parent_span_id})

            # 3. B3-Header prüfen (Zipkin/Sleuth)
            elif request.headers.get('X-B3-TraceId'):
                trace_id = request.headers.get('X-B3-TraceId')
                parent_span_id = request.headers.get('X-B3-SpanId')
                if not parent_span_id:
                    parent_span_id = 'unset'
                span_id = str(uuid.uuid4()).replace('-', '')[:16]
                logger.debug(f"Trace-Kontext aus B3-Header extrahiert",
                          extra={'trace_id': trace_id, 'span_id': span_id, 'parent_span_id': parent_span_id})

            # 4. Spring Cloud Sleuth Header für Trace-ID
            elif request.headers.get('X-Trace-Id'):
                trace_id = request.headers.get('X-Trace-Id')
                parent_span_id = request.headers.get('X-Span-Id')
                if not parent_span_id:
                    parent_span_id = 'unset'
                span_id = str(uuid.uuid4()).replace('-', '')[:16]
                logger.debug(f"Trace-Kontext aus Spring-Header extrahiert",
                          extra={'trace_id': trace_id, 'span_id': span_id, 'parent_span_id': parent_span_id})
    except Exception:
        # Fallback, wenn wir nicht in einem Flask-Request-Kontext sind
        pass

    # Wenn kein Kontext gefunden wurde, neuen erstellen
    if not trace_id:
        trace_id = str(uuid.uuid4()).replace('-', '')
        span_id = str(uuid.uuid4()).replace('-', '')[:16]
        parent_span_id = 'unset'
        logger.debug("Neuer Trace-Kontext erstellt",
                  extra={'trace_id': trace_id, 'span_id': span_id, 'parent_span_id': parent_span_id})

    return trace_id, span_id, parent_span_id

# Direktes Setup eines Standard-Loggers beim Import
default_logger = setup_logger()