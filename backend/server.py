"""DeepRecall FastAPI Server.

Main entry point for the DeepRecall API server. Handles initialization
of all core systems and middleware configuration.
"""

import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from core.config import get_settings
from core.logging_config import setup_logging
from app.websocket import get_connection_manager
from app.routes import ingestion_router, chat_router, system_router, aws_ingestion_router
from app.middleware.rate_limit import RateLimitMiddleware
from app.bootstrap import lifespan

# Configure logging before anything else
setup_logging(level="INFO")
log = logging.getLogger(__name__)


# Initialize FastAPI app
app = FastAPI(title="DeepRecall API", lifespan=lifespan)

# Add rate limiting middleware (MUST be added before CORS)
app.add_middleware(RateLimitMiddleware)

# Configure CORS with explicit origins (not wildcards)
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(ingestion_router)
app.include_router(chat_router)
app.include_router(system_router)
app.include_router(aws_ingestion_router)


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    """WebSocket endpoint for real-time pipeline updates."""
    mgr = get_connection_manager()
    await mgr.connect(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        mgr.disconnect(ws)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
