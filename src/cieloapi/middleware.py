import uuid
import threading

# Thread-local para pasar el correlation_id a cualquier parte del codigo
_correlation_id = threading.local()


def get_correlation_id() -> str:
    """Retorna el correlation_id del request actual. Util desde services y tasks."""
    return getattr(_correlation_id, "value", "-")


def set_correlation_id(value: str):
    _correlation_id.value = value


class CorrelationIDMiddleware:
    """
    Middleware que genera o propaga un Correlation ID por request.

    - Si el bot envia X-Correlation-ID, lo reutiliza (permite trazar end-to-end)
    - Si no, genera uno nuevo (UUID4)
    - Lo agrega al response header para que el bot lo reciba

    El ID queda disponible via get_correlation_id() en todo el ciclo del request,
    incluyendo services y tasks Celery (si se pasa como parametro).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        correlation_id = request.META.get("HTTP_X_CORRELATION_ID") or str(uuid.uuid4())
        set_correlation_id(correlation_id)
        request.correlation_id = correlation_id

        response = self.get_response(request)
        response["X-Correlation-ID"] = correlation_id
        return response
