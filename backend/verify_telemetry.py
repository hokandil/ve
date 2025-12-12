
import sys
import os
import logging
sys.path.append(os.getcwd())

# Mock settings to enable OTel
from unittest.mock import patch
with patch('app.core.config.settings.OTEL_ENABLED', True):
    try:
        from app.core.telemetry import setup_telemetry, get_tracer, get_meter
        from fastapi import FastAPI
        
        app = FastAPI()
        setup_telemetry(app)
        
        tracer = get_tracer()
        meter = get_meter()
        
        with tracer.start_as_current_span("test_span"):
            logging.info("Test log message")
            counter = meter.create_counter("test_counter")
            counter.add(1)
            
        print("Telemetry setup verified successfully")
    except Exception as e:
        print(f"Telemetry setup failed: {e}")
        sys.exit(1)
