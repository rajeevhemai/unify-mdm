"""
Production startup script for Azure App Service.
Serves both the FastAPI backend and the built React frontend.
"""

import os
import uvicorn
from app.main import app
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Serve React build files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    # Serve static assets (JS, CSS, images)
    app.mount("/assets", StaticFiles(directory=os.path.join(static_dir, "assets")), name="assets")

    # Catch-all route for React SPA - must be last
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve the React SPA for any non-API route."""
        # Don't intercept API routes
        if full_path.startswith("api/") or full_path in ("docs", "openapi.json", "health"):
            return
        file_path = os.path.join(static_dir, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(static_dir, "index.html"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("startup:app", host="0.0.0.0", port=port)
