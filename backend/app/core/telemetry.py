"""
OpenTelemetry Instrumentation for VE SaaS Backend
Provides distributed tracing across Chat -> Backend -> Gateway -> Agent
"""
import logging
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from app.core.config import settings

logger = logging.getLogger(__name__)

def setup_telemetry(app):
    """
    Setup OpenTelemetry instrumentation for the FastAPI app
    """
    if not settings.OTEL_ENABLED:
        logger.info("OpenTelemetry is disabled")
        return
    
    # Create resource with service name
    resource = Resource(attributes={
        SERVICE_NAME: "ve-saas-backend"
    })
    
    # Setup tracer provider
    provider = TracerProvider(resource=resource)
    
    # Configure OTLP exporter (sends to Jaeger/Tempo)
    otlp_exporter = OTLPSpanExporter(
        endpoint=settings.OTEL_EXPORTER_ENDPOINT,
        insecure=True  # Use TLS in production
    )
    
    # Add span processor
    provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    
    # Set as global tracer provider
    trace.set_tracer_provider(provider)
    
    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(app)
    
    # Instrument HTTPX (for Agent Gateway calls)
    HTTPXClientInstrumentor().instrument()
    
    logger.info(f"OpenTelemetry initialized, exporting to {settings.OTEL_EXPORTER_ENDPOINT}")

def get_tracer():
    """Get the tracer for manual instrumentation"""
    return trace.get_tracer(__name__)
