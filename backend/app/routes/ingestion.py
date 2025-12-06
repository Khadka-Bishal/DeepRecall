"""Document ingestion endpoint."""

import os
import shutil
import logging
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException

from app.state import get_ingestion_pipeline, get_observability
from app.services import get_benchmark, clear_all_caches
from app.websocket import get_connection_manager

log = logging.getLogger(__name__)
router = APIRouter(tags=["ingestion"])


@router.post("/ingest")
async def ingest_document(file: UploadFile = File(...)):
    """Process and index an uploaded document."""
    pipeline = get_ingestion_pipeline()
    benchmark = get_benchmark()
    obs = get_observability()
    ws = get_connection_manager()

    temp_path = Path(f"temp_{file.filename}")

    try:
        await ws.broadcast(
            {"type": "pipeline", "stage": "UPLOADING", "status": "active"}
        )

        with temp_path.open("wb") as f:
            shutil.copyfileobj(file.file, f)

        file_size = temp_path.stat().st_size
        await ws.broadcast(
            {"type": "pipeline", "stage": "UPLOADING", "status": "complete"}
        )
        await ws.broadcast(
            {"type": "pipeline", "stage": "PARTITIONING", "status": "active"}
        )

        benchmark.start_timer()
        result = await pipeline.run(str(temp_path), manager=ws)
        duration = benchmark.end_timer()

        docs = result["documents"]
        report = result["report"]

        benchmark.benchmark_ingestion(str(temp_path), result, duration)

        if obs:
            throughput = (file_size / 1024 / 1024) / duration if duration > 0 else 0
            obs.log_metrics(
                {
                    "ingestion/duration_s": round(duration, 2),
                    "ingestion/throughput_mbs": round(throughput, 2),
                    "ingestion/chunks": len(docs),
                    "ingestion/size_mb": round(file_size / 1024 / 1024, 2),
                }
            )

        await ws.broadcast(
            {
                "type": "pipeline",
                "stage": "COMPLETE",
                "status": "complete",
                "images": report.get("total_images", 0),
                "tables": report.get("total_tables", 0),
            }
        )

        clear_all_caches()

        throughput = (file_size / 1024 / 1024) / duration if duration > 0 else 0
        return {
            "status": "success",
            "filename": file.filename,
            "pipeline_report": report,
            "performance": {
                "duration_seconds": round(duration, 2),
                "throughput_mb_s": round(throughput, 2),
            },
        }

    except Exception:
        log.exception("ingestion failed")
        raise HTTPException(status_code=500, detail="Ingestion failed")
    finally:
        if temp_path.exists():
            temp_path.unlink()
