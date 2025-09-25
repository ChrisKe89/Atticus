"""Telemetry helpers for OpenTelemetry configuration."""

from __future__ import annotations

import logging

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter, SimpleSpanProcessor
from opentelemetry.sdk.trace.sampling import ParentBased, TraceIdRatioBased

from .config import AppSettings

_DEFAULT_ENDPOINT = "http://localhost:4318/v1/traces"
_CONFIG_STATE: dict[str, bool] = {"configured": False}


def configure_telemetry(settings: AppSettings, logger: logging.Logger | None = None) -> None:
    """Initialise OpenTelemetry exporters if enabled."""

    if _CONFIG_STATE["configured"] or not settings.telemetry_enabled:
        return

    endpoint = settings.otel_endpoint or _DEFAULT_ENDPOINT
    resource = Resource.create({"service.name": settings.otel_service_name})
    ratio = min(max(settings.otel_trace_ratio, 0.0), 1.0)
    sampler = ParentBased(TraceIdRatioBased(ratio))
    provider = TracerProvider(resource=resource, sampler=sampler)

    headers = settings.otel_headers_map or None
    exporter = OTLPSpanExporter(endpoint=endpoint, headers=headers)
    provider.add_span_processor(BatchSpanProcessor(exporter))

    if settings.otel_console_export:
        provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))

    trace.set_tracer_provider(provider)
    _CONFIG_STATE["configured"] = True

    if logger is not None:
        logger.info(
            "telemetry_configured",
            extra={
                "extra_payload": {
                    "endpoint": endpoint,
                    "service_name": settings.otel_service_name,
                    "console_export": settings.otel_console_export,
                    "trace_ratio": ratio,
                }
            },
        )


def get_tracer(name: str = "atticus") -> trace.Tracer:
    """Return the global tracer (configured lazily)."""

    return trace.get_tracer(name)
