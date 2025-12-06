"""Performance benchmarking for ingestion and retrieval."""

import time
import json
import os
from datetime import datetime
import statistics
from typing import Dict, Any, List, Optional
import psutil


class Benchmark:
    """Singleton for tracking ingestion and retrieval performance."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Benchmark, cls).__new__(cls)
            cls._instance.metrics = {
                "ingestion_runs": [],
                "retrieval_runs": [],
                "summary": {},
            }
            cls._instance.timer_start_time = None
            cls._instance.process = psutil.Process()
            cls._instance.first_ingestion = True
            cls._instance.first_retrieval = True
        return cls._instance

    def start_timer(self):
        """Start a timing window."""
        self.timer_start_time = time.perf_counter()

    def end_timer(self) -> float:
        """Stop the timer and return elapsed seconds."""
        if not self.timer_start_time:
            return 0
        duration = time.perf_counter() - self.timer_start_time
        self.timer_start_time = None
        return duration

    def benchmark_ingestion(self, file_path: str, result: Dict, duration: float):
        """Record metrics for an ingestion run."""
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        memory_info = self.process.memory_info()

        self.metrics["ingestion_runs"].append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "file_size_mb": round(file_size_mb, 4),
                "duration_seconds": round(duration, 4),
                "throughput_mb_s": (
                    round(file_size_mb / duration, 4) if duration > 0 else 0
                ),
                "num_chunks": len(result.get("documents", [])),
                "memory_mb": round(memory_info.rss / 1024 / 1024, 2),
                "is_cold_start": self.first_ingestion,
            }
        )

        if self.first_ingestion:
            self.first_ingestion = False

        self.update_summary()

    def benchmark_retrieval(
        self, query: str, num_results: int, duration: float, scores: List[float]
    ):
        """Record metrics for a retrieval run."""
        memory_info = self.process.memory_info()

        self.metrics["retrieval_runs"].append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "query": query,
                "num_results": num_results,
                "latency_ms": round(duration * 1000, 4),
                "avg_score": statistics.mean(scores) if scores else 0,
                "min_score": min(scores) if scores else 0,
                "max_score": max(scores) if scores else 0,
                "memory_mb": round(memory_info.rss / 1024 / 1024, 2),
                "is_cold_start": self.first_retrieval,
            }
        )

        if self.first_retrieval:
            self.first_retrieval = False

        self.update_summary()

    def update_summary(self):
        """Refresh cached summary statistics."""
        # Ingestion summary
        ingestion_runs = self.metrics["ingestion_runs"]
        if ingestion_runs:
            durations = [r["duration_seconds"] for r in ingestion_runs]
            throughputs = [r["throughput_mb_s"] for r in ingestion_runs]
            memories = [r["memory_mb"] for r in ingestion_runs]

            self.metrics["summary"]["ingestion"] = {
                "total_runs": len(ingestion_runs),
                "avg_duration_seconds": round(statistics.mean(durations), 4),
                "p50_duration_seconds": round(statistics.median(durations), 4),
                "p95_duration_seconds": (
                    round(statistics.quantiles(durations, n=20)[18], 4)
                    if len(durations) > 1
                    else round(durations[0], 4)
                ),
                "p99_duration_seconds": (
                    round(statistics.quantiles(durations, n=100)[98], 4)
                    if len(durations) > 1
                    else round(durations[0], 4)
                ),
                "avg_throughput_mb_s": round(statistics.mean(throughputs), 4),
                "avg_memory_mb": round(statistics.mean(memories), 4),
                "peak_memory_mb": round(max(memories), 2),
            }

        # Retrieval summary
        retrieval_runs = self.metrics["retrieval_runs"]
        if retrieval_runs:
            latencies = [r["latency_ms"] for r in retrieval_runs]
            scores = [r["avg_score"] for r in retrieval_runs]
            memories = [r["memory_mb"] for r in retrieval_runs]

            self.metrics["summary"]["retrieval"] = {
                "total_runs": len(retrieval_runs),
                "avg_latency_ms": round(statistics.mean(latencies), 4),
                "p50_latency_ms": round(statistics.median(latencies), 4),
                "p95_latency_ms": (
                    round(statistics.quantiles(latencies, n=20)[18], 4)
                    if len(latencies) > 1
                    else round(latencies[0], 4)
                ),
                "p99_latency_ms": (
                    round(statistics.quantiles(latencies, n=100)[98], 4)
                    if len(latencies) > 1
                    else round(latencies[0], 4)
                ),
                "avg_score": round(statistics.mean(scores), 4),
                "avg_memory_mb": round(statistics.mean(memories), 4),
            }

    def save_report(self, output_dir: str = "benchmarks") -> str:
        """Persist the current metrics to disk."""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        file_path = os.path.join(output_dir, f"benchmark_report_{timestamp}.json")

        with open(file_path, "w") as f:
            json.dump(self.metrics, f, indent=4)
        return file_path

    def print_summary(self):
        """Print a summary of the benchmark metrics."""
        print("\n--- Benchmark Summary ---")
        if "ingestion" in self.metrics["summary"]:
            print("\nIngestion:")
            for key, value in self.metrics["summary"]["ingestion"].items():
                print(f"  {key.replace('_', ' ').title()}: {value}")

        if "retrieval" in self.metrics["summary"]:
            print("\nRetrieval:")
            for key, value in self.metrics["summary"]["retrieval"].items():
                print(f"  {key.replace('_', ' ').title()}: {value}")
        print("\n-------------------------\n")


# Singleton instance
_benchmark_instance: Optional[Benchmark] = None


def get_benchmark() -> Benchmark:
    """Return the singleton benchmark instance."""
    global _benchmark_instance
    if _benchmark_instance is None:
        _benchmark_instance = Benchmark()
    return _benchmark_instance
