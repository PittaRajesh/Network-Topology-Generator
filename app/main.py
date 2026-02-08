"""
Networking Automation Engine

An AI-assisted networking automation tool that automatically generates L2/L3 network
topologies, creates routing configurations, and prepares scalable test environments
for regression and automation testing.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from app.config import settings
from app.api import router as api_router

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Include API routes
app.include_router(api_router)


@app.get(
    "/",
    tags=["health"],
    summary="Health Check",
    description="API health status endpoint"
)
async def health_check() -> dict:
    """
    Health check endpoint.
    
    Returns:
        Dictionary with service status
    """
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
    }


@app.get(
    "/api/v1/info",
    tags=["info"],
    summary="API Information",
    description="Get API version and capabilities"
)
async def api_info() -> dict:
    """
    Get API information and capabilities.
    
    Returns:
        Dictionary with API details
    """
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "description": settings.app_description,
        "capabilities": [
            "Automatic topology generation",
            "OSPF configuration generation",
            "Containerlab export",
            "YAML topology export",
            "Device configuration rendering",
            "Topology statistics and analysis",
            "AI-assisted topology analysis (SPOF detection, path balancing, metrics)",
            "Failure simulation and impact analysis",
            "Resilience test scenario generation",
            "Topology optimization recommendations",
            "Intent-Based Networking (IBN) - High-level intent to topology mapping",
            "Automatic topology generation from user intent",
            "Intent validation and constraint satisfaction reporting",
            "Support for hub-spoke, full mesh, ring, tree, and leaf-spine topologies",
        ],
        "supported_protocols": ["ospf"],
        "future_protocols": ["bgp", "isis"],
    }


def custom_openapi():
    """Customize OpenAPI schema."""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=settings.app_name,
        version=settings.app_version,
        description=settings.app_description,
        routes=app.routes,
    )
    
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Server will run on {settings.host}:{settings.port}")
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
