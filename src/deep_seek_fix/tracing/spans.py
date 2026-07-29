from collections.abc import Iterator
from contextlib import contextmanager

from opentelemetry import trace


@contextmanager
def dsfix_span(name: str, **attributes: object) -> Iterator[None]:
    tracer = trace.get_tracer("deep_seek_fix")
    with tracer.start_as_current_span(name) as span:
        for key, value in attributes.items():
            span.set_attribute(key, str(value))
        yield
