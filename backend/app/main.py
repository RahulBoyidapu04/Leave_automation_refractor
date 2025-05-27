from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from dotenv import load_dotenv
import logging
import time
import os
import traceback

# Configure logging with more detailed format for production
logging.basicConfig(
    level=logging.INFO if os.getenv("ENVIRONMENT", "development") != "production" else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load .env variables
load_dotenv()

# Request ID middleware for tracking requests
class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", None)
        if request_id is None:
            import uuid
            request_id = str(uuid.uuid4())
        
        # Add request_id to all log contexts for this request
        logger.info(f"Request {request_id} started: {request.method} {request.url.path}")
        start_time = time.time()
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)
            logger.info(f"Request {request_id} completed in {process_time:.4f}s - Status: {response.status_code}")
            return response
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(f"Request {request_id} failed after {process_time:.4f}s: {str(e)}")
            return JSONResponse(
                status_code=500, 
                content={"detail": "Internal server error", "request_id": request_id}
            )

# Application setup
app = FastAPI(
    title="Leave Automation System API", 
    version="1.0.0",
    description="API for managing employee leave requests and approvals",
    docs_url="/api/docs" if os.getenv("ENVIRONMENT", "development") != "production" else None,
    redoc_url="/api/redoc" if os.getenv("ENVIRONMENT", "development") != "production" else None
)

# CORS setup - restrict in production
origins = ["*"]  # In production, replace with specific domains
if os.getenv("ENVIRONMENT") == "production":
    origins = [
        os.getenv("FRONTEND_URL", "https://leave.company.com"),
        # Add other trusted origins here
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add request tracking middleware
app.add_middleware(RequestIDMiddleware)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_id = str(time.time())
    logger.error(f"Global exception handler caught: {str(exc)}")
    logger.error(f"Error ID: {error_id}")
    logger.error(traceback.format_exc())
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An unexpected error occurred",
            "error_id": error_id
        }
    )

# Import routers - after middleware setup
from .auth import router as auth_router
from .routes import router as core_router  # router already has tags=["Core"] in its definition
from .admin_routes import router as admin_router
from .notifications_routes import router as notif_router
from .reporting_routes import router as report_router
from app.logic import ValidationError, LeaveProcessingError  # <-- import your custom exceptions

# Mount routers
app.include_router(auth_router)
logger.info("✅ Mounted Auth Router")

app.include_router(core_router)  # No need to set tags again
logger.info("✅ Mounted Core Router")

app.include_router(admin_router, prefix="/admin", tags=["Admin"])
logger.info("✅ Mounted Admin Router")

app.include_router(notif_router, tags=["Notifications"])
logger.info("✅ Mounted Notifications Router")

app.include_router(report_router, prefix="/reports", tags=["Reports"])
logger.info("✅ Mounted Reports Router")

@app.get("/")
def root():
    """Root endpoint to verify API is running"""
    logger.info("Root endpoint accessed")
    return {
        "message": "Leave Automation API is running", 
        "version": "1.0.0",
        "status": "healthy"
    }

@app.get("/health")
def health_check():
    """Health check endpoint for load balancers and monitoring"""
    return {"status": "healthy"}

# Add a debug endpoint to see all registered routes - only in development
if os.getenv("ENVIRONMENT", "development") != "production":
    @app.get("/debug/routes")
    def get_routes():
        """Debug endpoint to see all registered routes"""
        routes = []
        for route in app.routes:
            routes.append({
                "path": route.path,
                "name": route.name,
                "methods": route.methods
            })
        return {"routes": routes}

@app.on_event("startup")
async def startup_event():
    """Log all routes on startup for debugging"""
    environment = os.getenv("ENVIRONMENT", "development")
    logger.info(f"Starting Leave Automation API in {environment} mode...")
    
    if environment != "production":
        logger.info("Registered routes:")
        for route in app.routes:
            logger.info(f"Route: {route.path}, Methods: {route.methods}")



@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=400,
        content={
            "message": str(exc),
            "status": "error",
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(LeaveProcessingError)
async def processing_exception_handler(request: Request, exc: LeaveProcessingError):
    return JSONResponse(
        status_code=422,
        content={
            "message": str(exc),
            "status": "error",
            "timestamp": datetime.now().isoformat()
        }
    )