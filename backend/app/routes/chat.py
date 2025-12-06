import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.schemas import QueryRequest
from app.services import get_benchmark, get_retrieval_cache, get_answer_cache
from app.state import get_retriever_system, get_observability

router = APIRouter(prefix="", tags=["chat"])


@router.post("/chat")
async def chat(request: QueryRequest):
    ret = get_retriever_system()
    bm = get_benchmark()
    obs = get_observability()
    rcache = get_retrieval_cache()
    acache = get_answer_cache()

    cache_st = {"retrieval": "miss", "answer": "miss"}

    try:
        # check answer cache
        ans, hit = acache.get(request.query, prefix="answer")
        if hit:
            cache_st = {"retrieval": "hit", "answer": "hit"}
            return {
                "role": "assistant",
                "content": ans["content"],
                "retrievedChunks": ans["chunks"],
                "performance": {
                    "retrieval_latency_ms": 0,
                    "num_results": len(ans["chunks"]),
                    "cache_status": cache_st,
                },
            }

        # check retrieval cache
        cached, hit = rcache.get(request.query, prefix="retrieval")
        if hit:
            cache_st["retrieval"] = "hit"
            results, queries = cached
            dur = 0
        else:
            bm.start_timer()
            results, queries = await ret.aretrieve_with_details(request.query)
            dur = bm.end_timer()
            rcache.set(request.query, (results, queries), prefix="retrieval")

        chunks = []
        for item in results:
            doc = item["document"]
            orig = json.loads(doc.metadata.get("original_content", "{}"))
            chunks.append(
                {
                    "id": doc.metadata.get("chunk_id", "unknown"),
                    "content": orig.get("raw_text", ""),
                    "images": orig.get("images_base64", []),
                    "score": item.get("score", 0.0),
                    "scores": item.get("scores", {"bm25": 0.0, "vector": 0.0}),
                    "page": doc.metadata.get("page_number", 1),
                }
            )

        answer = await ret.agenerate_answer(request.query, results)
        acache.set(
            request.query, {"content": answer, "chunks": chunks}, prefix="answer"
        )

        if cache_st["retrieval"] == "miss":
            scores = [item["score"] for item in results]
            bm.benchmark_retrieval(request.query, len(results), dur, scores)
            if obs:
                obs.log_metrics(
                    {
                        "retrieval/latency_ms": round(dur * 1000, 2),
                        "retrieval/num_results": len(results),
                        "retrieval/avg_score": (
                            sum(scores) / len(scores) if scores else 0
                        ),
                    }
                )

        return {
            "role": "assistant",
            "content": answer,
            "retrievedChunks": chunks,
            "performance": {
                "retrieval_latency_ms": round(dur * 1000, 2),
                "num_results": len(results),
                "cache_status": cache_st,
            },
        }

    except Exception:
        raise HTTPException(status_code=500, detail="Request failed")


@router.post("/chat/stream")
async def chat_stream(request: QueryRequest):
    """SSE streaming endpoint."""
    retriever_system = get_retriever_system()

    retrieval_cache = get_retrieval_cache()

    async def generate():
        try:
            cached_retrieval, hit = retrieval_cache.get(
                request.query, prefix="retrieval"
            )
            if hit:
                detailed_results, expanded_queries = cached_retrieval
            else:
                detailed_results, expanded_queries = (
                    await retriever_system.aretrieve_with_details(request.query)
                )
                retrieval_cache.set(
                    request.query,
                    (detailed_results, expanded_queries),
                    prefix="retrieval",
                )

            chunks_payload = []
            for item in detailed_results:
                doc = item["document"]
                orig = json.loads(doc.metadata.get("original_content", "{}"))
                chunks_payload.append(
                    {
                        "id": doc.metadata.get("chunk_id", "unknown"),
                        "content": orig.get("raw_text", ""),
                        "images": orig.get("images_base64", []),
                        "score": item.get("score", 0.0),
                        "scores": item.get("scores", {"bm25": 0.0, "vector": 0.0}),
                        "page": doc.metadata.get("page_number", 1),
                    }
                )

            full_answer = ""
            async for token in retriever_system.agenerate_answer_stream(
                request.query, detailed_results
            ):
                full_answer += token
                yield f"data: {json.dumps({'type': 'token', 'data': token})}\n\n"

            yield f"data: {json.dumps({'type': 'done', 'data': full_answer})}\n\n"
            yield f"data: {json.dumps({'type': 'queries', 'data': expanded_queries})}\n\n"
            yield f"data: {json.dumps({'type': 'chunks', 'data': chunks_payload})}\n\n"

        except Exception:
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
