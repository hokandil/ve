"""
Minimal VE SaaS Platform - FastAPI Backend
Main application entry point
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import logging

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

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now
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
        content={"detail": str(exc)}
    )

# Try to include routers, but don't fail if they don't exist
logger.info("🔄 Loading API routers...")
try:
    logger.info("  Importing modules...")
    from app.api import tasks, workflows, workflow_control, discovery, marketplace, auth, customer, messages, billing, webhooks
    logger.info("  ✅ All modules imported successfully")
    
    logger.info("  Registering routers...")
    app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
    logger.info("    ✅ auth router")
    app.include_router(tasks.router)
    logger.info("    ✅ tasks router")
    app.include_router(workflows.router)
    logger.info("    ✅ workflows router")
    app.include_router(workflow_control.router)
    logger.info("    ✅ workflow_control router")
    app.include_router(discovery.router, prefix="/api/discovery", tags=["discovery"])
    logger.info("    ✅ discovery router")
    app.include_router(marketplace.router, prefix="/api/marketplace", tags=["marketplace"])
    logger.info("    ✅ marketplace router")
    app.include_router(customer.router, prefix="/api/customer", tags=["customer"])
    logger.info("    ✅ customer router")
    app.include_router(messages.router)
    logger.info("    ✅ messages router")
    app.include_router(billing.router, prefix="/api/billing", tags=["billing"])
    logger.info("    ✅ billing router")
    app.include_router(webhooks.router)
    logger.info("    ✅ webhooks router")
    
    logger.info("✅ All routers loaded successfully")
except Exception as e:
    logger.error(f"❌ Error loading routers: {e}", exc_info=True)
    # Try to load at least the basic ones
    try:
        logger.info("  Attempting to load basic routers only...")
        from app.api import tasks, workflows, workflow_control
        app.include_router(tasks.router)
        app.include_router(workflows.router)
        app.include_router(workflow_control.router)
        logger.info("✅ Basic routers loaded")
    except Exception as e2:
        logger.error(f"❌ Failed to load basic routers: {e2}", exc_info=True)

@app.get("/")
async def root():
    return {
        "message": "VE SaaS Platform API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
