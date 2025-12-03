"""
VE SaaS Platform - FastAPI Backend
Main application entry point
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import logging

from app.core.config import settings
from app.api import auth, tasks, billing, marketplace, customer, messages, webhooks, discovery

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="VE SaaS Platform API",
    description="AI-Powered Virtual Employee Marketplace",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Setup OpenTelemetry
from app.core.telemetry import setup_telemetry
setup_telemetry(app)

# Setup Redis cache
from app.core.cache import init_cache
init_cache(settings.REDIS_URL)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    logger.info(f"{request.method} {request.url.path} - {process_time:.3f}s")
    return response

# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(tasks.router)
app.include_router(billing.router, prefix="/api/billing", tags=["billing"])
app.include_router(marketplace.router, prefix="/api/marketplace", tags=["marketplace"])
app.include_router(customer.router, prefix="/api/customer", tags=["customer"])
app.include_router(messages.router)
app.include_router(webhooks.router)
app.include_router(discovery.router, prefix="/api/discovery", tags=["discovery"])

@app.get("/")
async def root():
    return {
        "message": "VE SaaS Platform API",
        "version": "1.0.0",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
