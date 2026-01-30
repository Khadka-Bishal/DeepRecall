"""Chat and query endpoints for DeepRecall."""

import json
import logging
from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import StreamingResponse

from app.schemas import QueryRequest
from app.services import get_benchmark, get_retrieval_cache, get_answer_cache
from app.state import get_retriever_system, get_observability
from .utils import format_chunks_response

log = logging.getLogger(__name__)
router = APIRouter(prefix="", tags=["chat"])


@router.post("/chat")
async def chat(
    request: QueryRequest,
    x_session_id: str = Header(..., alias="X-Session-ID")
):
    """Process a query and return an answer with retrieved chunks."""
    retriever = get_retriever_system()
    benchmark = get_benchmark()
    obs = get_observability()
    rcache = get_retrieval_cache()
    acache = get_answer_cache()

    # Scope cache key by session to prevent data leak
    cache_key = f"{x_session_id}:{request.query}"

    cache_status = {"retrieval": "miss", "answer": "miss"}

    try:
        # Check answer cache first
        cached_answer, hit = acache.get(cache_key, prefix="answer")
        if hit:
            return {
                "role": "assistant",
                "content": cached_answer["content"],
                "retrievedChunks": cached_answer["chunks"],
                "performance": {
                    "retrieval_latency_ms": 0,
                    "num_results": len(cached_answer["chunks"]),
                    "cache_status": {"retrieval": "hit", "answer": "hit"},
                },
            }

        # Check retrieval cache
        cached_retrieval, hit = rcache.get(cache_key, prefix="retrieval")
        if hit:
            cache_status["retrieval"] = "hit"
            results, queries = cached_retrieval
            duration = 0
        else:
            benchmark.start_timer()
            # Pass session_id filter to retriever
            results, queries = await retriever.aretrieve_with_details(
                request.query, filters={"session_id": x_session_id}
            )
            duration = benchmark.end_timer()
            rcache.set(cache_key, (results, queries), prefix="retrieval")

        # Format chunks using shared utility
        chunks = format_chunks_response(results)

        # Generate answer
        answer = await retriever.agenerate_answer(request.query, results)
        acache.set(
            cache_key, {"content": answer, "chunks": chunks}, prefix="answer"
        )

        # Log metrics
        if cache_status["retrieval"] == "miss":
            scores = [item["score"] for item in results]
            benchmark.benchmark_retrieval(request.query, len(results), duration, scores)
            if obs:
                obs.log_metrics({
                    "retrieval/latency_ms": round(duration * 1000, 2),
                    "retrieval/num_results": len(results),
                    "retrieval/avg_score": sum(scores) / len(scores) if scores else 0,
                })

        return {
            "role": "assistant",
            "content": answer,
            "retrievedChunks": chunks,
            "performance": {
                "retrieval_latency_ms": round(duration * 1000, 2),
                "num_results": len(results),
                "cache_status": cache_status,
            },
        }

    except Exception:
        log.exception("Chat request failed")
        raise HTTPException(status_code=500, detail="Request failed")


@router.post("/chat/stream")
async def chat_stream(
    request: QueryRequest, 
    x_session_id: str = Header(..., alias="X-Session-ID")
):
    """SSE streaming endpoint for chat with real-time token output."""
    retriever = get_retriever_system()
    rcache = get_retrieval_cache()

    # Scope cache key by session to prevent data leak
    cache_key = f"{x_session_id}:{request.query}"

    async def generate():
        try:
            # Check retrieval cache
            cached, hit = rcache.get(cache_key, prefix="retrieval")
            if hit:
                results, expanded_queries = cached
            else:
                results, expanded_queries = await retriever.aretrieve_with_details(
                    request.query, filters={"session_id": x_session_id}
                )
                rcache.set(cache_key, (results, expanded_queries), prefix="retrieval")

            # Format chunks using shared utility
            chunks = format_chunks_response(results)

            # Send metadata events FIRST (Better UX)
            yield f"data: {json.dumps({'type': 'queries', 'queries': expanded_queries})}\n\n"
            yield f"data: {json.dumps({'type': 'chunks', 'chunks': chunks})}\n\n"

            # Stream answer tokens
            full_answer = ""
            async for token in retriever.agenerate_answer_stream(request.query, results):
                full_answer += token
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

            # Send final done event
            yield f"data: {json.dumps({'type': 'done', 'content': full_answer})}\n\n"

        except Exception:
            log.exception("Stream request failed")
            yield f"data: {json.dumps({'type': 'error', 'data': 'Request failed'})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
