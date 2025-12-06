import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from core.ingestion import IngestionPipeline
from core.retrieval import HybridRetrieverSystem
from app.state import get_app_state
from app.services import get_observability_manager
from app.websocket import get_connection_manager
from app.routes import ingestion_router, chat_router, system_router

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)


def _init_obs():
    if os.environ.get("DISABLE_OBSERVABILITY") == "true":
        return None
    try:
        obs = get_observability_manager()
        obs.setup_langsmith("DeepRecall")
        obs.setup_wandb(
            "deeprecall",
            config={
                "model": "gpt-4o-mini",
                "embedding_model": "text-embedding-3-small",
                "retrieval": "hybrid_rrf",
            },
        )
        return obs
    except Exception as e:
        log.warning("obs init skipped: %s", e)
        return None


@asynccontextmanager
async def lifespan(app: FastAPI):
    retriever = HybridRetrieverSystem()
    pipeline = IngestionPipeline(retriever_system=retriever)
    obs = _init_obs()

    get_app_state().initialize(retriever, pipeline, obs)
    log.info("app started")
    yield
    if obs:
        obs.finish()
    log.info("app stopped")


app = FastAPI(title="DeepRecall API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingestion_router)
app.include_router(chat_router)
app.include_router(system_router)


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    mgr = get_connection_manager()
    await mgr.connect(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        mgr.disconnect(ws)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
