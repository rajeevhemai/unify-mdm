"""
Production startup script for Railway/Azure App Service.
Serves both the FastAPI backend and the built React frontend.
"""
import os
import uvicorn
from fastapi import HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.main import app

# Serve React build files
static_dir = os.path.join(os.path.dirname(__file__), "static")

if os.path.exists(static_dir):
    # Serve static assets (JS, CSS, images)
    assets_dir = os.path.join(static_dir, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/")
    async def serve_index():
        """Serve the React SPA index page."""
        return FileResponse(os.path.join(static_dir, "index.html"))

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve the React SPA for any non-API route."""
        # Don't intercept API routes, docs, or health check
        if full_path.startswith("api/") or full_path in ("docs", "openapi.json", "health"):
            raise HTTPException(status_code=404)

        file_path = os.path.join(static_dir, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(static_dir, "index.html"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("startup:app", host="0.0.0.0", port=port)
