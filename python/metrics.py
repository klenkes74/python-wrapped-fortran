from prometheus_client import Counter, Histogram, Summary, multiprocess, CollectorRegistry
import os
import time

metrics_registry = CollectorRegistry()

def configure_metrics(app):
    """
    Konfiguriert die Prometheus-Metriken für die Flask-Anwendung.
    """
    if not app.config.get('ENABLE_PROMETHEUS', True):
        app.logger.info("Prometheus Metrics disabled")
        return app

    app.logger.info("Configuring Prometheus Metrics")

    # Multiprocess-Konfiguration
    multiprocess_dir = os.environ.get('PROMETHEUS_MULTIPROC_DIR', '/tmp/prometheus')
    if not os.path.exists(multiprocess_dir):
        os.makedirs(multiprocess_dir)

    multiprocess.MultiProcessCollector.multiprocess_dir = multiprocess_dir

    multiprocess.MultiProcessCollector(metrics_registry)

    return app

# HTTP-Request Metriken
http_requests_total = Counter(
    'http_requests_total',
    'Gesamtzahl der HTTP Requests',
    ['method', 'endpoint', 'status'],
    registry=metrics_registry
)

http_request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP Request Dauer in Sekunden',
    ['method', 'endpoint'],
    buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0),
    registry=metrics_registry
)

# Fortran-Wrapper Metriken
fortran_calls_total = Counter(
    'fortran_calls_total',
    'Gesamtzahl der Aufrufe an den Fortran-Rechner',
    ['function'],
    registry=metrics_registry
)

fortran_call_duration = Summary(
    'fortran_call_duration_seconds',
    'Fortran Aufrufdauer in Sekunden',
    ['function'],
    registry=metrics_registry
)

fortran_call_errors = Counter(
    'fortran_call_errors',
    'Anzahl der Fehler bei Fortran-Aufrufen',
    ['function', 'error_type'],
    registry=metrics_registry
)

# Decorator für HTTP-Request-Metriken
def track_request_metrics(view_func):
    from functools import wraps
    from flask import request, g

    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        # Zeitpunkt merken
        start_time = time.time()

        # View ausführen
        try:
            response = view_func(*args, **kwargs)
            status = response.status_code
        except Exception as e:
            # Bei Exception
            status = 500
            raise e
        finally:
            # Dauer berechnen
            duration = time.time() - start_time
            endpoint = request.endpoint or 'unknown'
            http_requests_total.labels(
                method=request.method,
                endpoint=endpoint,
                status=status
            ).inc()

            http_request_duration.labels(
                method=request.method,
                endpoint=endpoint
            ).observe(duration)

        return response

    return wrapped_view

# Decorator für Fortran-Wrapper-Metriken
def track_fortran_call(func):
    from functools import wraps

    @wraps(func)
    def wrapper(*args, **kwargs):
        function_name = func.__name__
        start_time = time.time()

        try:
            result = func(*args, **kwargs)
            fortran_calls_total.labels(function=function_name).inc()
            return result
        except Exception as e:
            error_type = type(e).__name__
            fortran_call_errors.labels(function=function_name, error_type=error_type).inc()
            raise
        finally:
            duration = time.time() - start_time
            fortran_call_duration.labels(function=function_name).observe(duration)

    return wrapper
