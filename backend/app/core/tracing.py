"""
OpenTelemetry Configuration for Temporal Workflows
Exports traces to OpenObserve for delegation tree visualization
"""
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.temporalio import TemporalioInstrumentor
import os

def setup_tracing():
    """
    Configure OpenTelemetry tracing for Temporal workflows.
    Exports to OpenObserve for visualization.
    """
    # Create resource with service information
    resource = Resource.create({
        "service.name": "ve-temporal-worker",
        "service.version": "1.0.0",
        "deployment.environment": os.getenv("ENVIRONMENT", "development")
    })
    
    # Create tracer provider
    provider = TracerProvider(resource=resource)
    
    # Configure OTLP exporter to OpenObserve
    otlp_exporter = OTLPSpanExporter(
        endpoint=os.getenv("OPENOBSERVE_OTLP_ENDPOINT", "http://openobserve:5080"),
        headers={
            "Authorization": f"Basic {os.getenv('OPENOBSERVE_AUTH_TOKEN', '')}",
            "organization": os.getenv("OPENOBSERVE_ORG", "default"),
            "stream-name": "temporal-traces"
        }
    )
    
    # Add batch processor
    provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    
    # Set as global tracer provider
    trace.set_tracer_provider(provider)
    
    # Instrument Temporal
    TemporalioInstrumentor().instrument()
    
    return trace.get_tracer(__name__)


def create_delegation_span(tracer, span_name: str, attributes: dict = None):
    """
    Create a span for delegation tracking.
    
    Args:
        tracer: OpenTelemetry tracer
        span_name: Name of the span (e.g., "agent_decision", "delegate_to_copywriter")
        attributes: Additional attributes to attach to span
    
    Returns:
        Span context manager
    """
    span = tracer.start_span(span_name)
    
    if attributes:
        for key, value in attributes.items():
            span.set_attribute(key, value)
    
    return span


# Global tracer instance
_tracer = None

def get_tracer():
    """Get or create the global tracer instance"""
    global _tracer
    if _tracer is None:
        _tracer = setup_tracing()
    return _tracer
