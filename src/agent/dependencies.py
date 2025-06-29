from a2a.server.request_handlers import DefaultRequestHandler

_request_handler: DefaultRequestHandler | None = None


def set_request_handler_instance(handler: DefaultRequestHandler):
    """Set the global request handler instance."""
    global _request_handler
    _request_handler = handler


def get_request_handler() -> DefaultRequestHandler:
    """Get the global request handler instance."""
    if _request_handler is None:
        raise RuntimeError("Request handler not initialized")
    return _request_handler 