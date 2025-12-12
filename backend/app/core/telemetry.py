"""
OpenTelemetry Instrumentation for VE SaaS Backend
Provides distributed tracing, metrics, and logs exporting to OpenObserve via OTLP
"""
import logging
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter

from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry._logs import set_logger_provider

from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from app.core.config import settings

logger = logging.getLogger(__name__)

def setup_telemetry(app):
    """
    Setup OpenTelemetry instrumentation for the FastAPI app
    Configures Traces, Metrics, and Logs to export to OpenObserve via OTLP
    """
    if not settings.OTEL_ENABLED:
        logger.info("OpenTelemetry is disabled")
        return
    
    # Create resource with service name
    resource = Resource(attributes={
        SERVICE_NAME: "ve-saas-backend",
        "deployment.environment": settings.ENVIRONMENT
    })
    
    # 1. TRACES Setup
    trace_provider = TracerProvider(resource=resource)
    otlp_trace_exporter = OTLPSpanExporter(
        endpoint=settings.OTEL_EXPORTER_ENDPOINT,
        insecure=True
    )
    trace_provider.add_span_processor(BatchSpanProcessor(otlp_trace_exporter))
    trace.set_tracer_provider(trace_provider)
    
    # 2. METRICS Setup
    otlp_metric_exporter = OTLPMetricExporter(
        endpoint=settings.OTEL_EXPORTER_ENDPOINT,
        insecure=True
    )
    metric_reader = PeriodicExportingMetricReader(otlp_metric_exporter)
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)
    
    # 3. LOGS Setup
    logger_provider = LoggerProvider(resource=resource)
    otlp_log_exporter = OTLPLogExporter(
        endpoint=settings.OTEL_EXPORTER_ENDPOINT,
        insecure=True
    )
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(otlp_log_exporter))
    set_logger_provider(logger_provider)
    
    # Hook Python logging to OTel
    LoggingInstrumentor().instrument(set_logging_format=True, log_level=logging.INFO)
    
    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(app, tracer_provider=trace_provider, meter_provider=meter_provider)
    
    # Instrument HTTPX (for Agent Gateway calls)
    HTTPXClientInstrumentor().instrument(tracer_provider=trace_provider)
    
    logger.info(f"OpenTelemetry initialized (Traces, Metrics, Logs) -> {settings.OTEL_EXPORTER_ENDPOINT}")

def get_tracer():
    """Get the tracer for manual instrumentation"""
    return trace.get_tracer(__name__)

def get_meter():
    """Get the meter for manual instrumentation"""
    return metrics.get_meter(__name__)
