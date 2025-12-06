from fastapi import APIRouter

from app.services import get_benchmark, get_cache_stats, clear_all_caches
from app.state import get_observability

router = APIRouter(tags=["system"])


@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "deeprecall-backend"}


@router.get("/cache/stats")
async def cache_stats():
    return get_cache_stats()


@router.post("/cache/clear")
async def cache_clear():
    result = clear_all_caches()
    print(f"caches cleared: {result}")
    return {"status": "success", **result}


@router.get("/benchmark")
async def get_benchmark_report():
    return get_benchmark().metrics


@router.post("/benchmark/save")
async def save_benchmark_report():
    """Save benchmark report to file and log to W&B."""
    benchmark = get_benchmark()
    observability = get_observability()

    output_path = benchmark.save_report()
    benchmark.print_summary()

    # Log to W&B if available
    if observability:
        observability.log_benchmark_results(benchmark.metrics)

    return {
        "status": "success",
        "report_path": output_path,
        "metrics": benchmark.metrics,
    }
