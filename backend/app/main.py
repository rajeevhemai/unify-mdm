"""
Unify - Master Data Management
Main FastAPI application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db
from app.api import upload, matching, golden_records, dashboard

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered Master Data Management - Single Source of Truth",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(dashboard.router)
app.include_router(upload.router)
app.include_router(matching.router)
app.include_router(golden_records.router)


@app.on_event("startup")
def on_startup():
    """Initialize database on startup."""
    init_db()


--@app.get("/")
--def root():
 --   return {
   --     "app": settings.APP_NAME,
     --   "version": settings.APP_VERSION,
       -- "docs": "/docs",
   -- }


@app.get("/health")
def health():
    return {"status": "healthy"}
