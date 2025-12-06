"""Observability integrations for LangSmith and Weights & Biases."""

import os
from typing import Optional, Dict, Any


class ObservabilityManager:
    """Manage LangSmith and W&B integrations."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ObservabilityManager, cls).__new__(cls)
            cls._instance.langsmith_enabled = False
            cls._instance.wandb_enabled = False
            cls._instance.wandb_run = None
        return cls._instance

    def setup_langsmith(self, project_name: str = "DeepRecall") -> bool:
        """Enable LangSmith tracing when credentials are present."""
        langchain_api_key = os.environ.get("LANGCHAIN_API_KEY")

        if not langchain_api_key:
            print("LANGCHAIN_API_KEY not found; LangSmith tracing disabled")
            return False

        # Enable LangSmith tracing
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
        os.environ["LANGCHAIN_PROJECT"] = project_name

        self.langsmith_enabled = True
        print(f"LangSmith tracing enabled for project: {project_name}")
        return True

    def setup_wandb(
        self,
        project_name: str = "deeprecall",
        entity: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Start a Weights & Biases run with the provided configuration."""
        try:
            import wandb
        except ImportError:
            print("wandb not installed; skipping instrumentation")
            return False

        # Initialize W&B
        try:
            self.wandb_run = wandb.init(
                project=project_name, entity=entity, config=config or {}, reinit=True
            )
            self.wandb_enabled = True
            print("Weights & Biases tracking enabled")
            print(f"Dashboard: {self.wandb_run.url}")
            return True
        except Exception as e:
            print(f"Failed to initialize W&B: {e}")
            return False

    def log_metrics(self, metrics: Dict[str, Any], step: Optional[int] = None):
        """Send metrics to W&B if instrumentation is enabled."""
        if not self.wandb_enabled:
            return

        try:
            import wandb

            wandb.log(metrics, step=step)
        except Exception as e:
            print(f"Failed to log metrics to W&B: {e}")

    def log_benchmark_results(self, benchmark_metrics: Dict[str, Any]):
        """Log benchmark aggregates to W&B when available."""
        if not self.wandb_enabled:
            return

        try:
            import wandb

            # Log ingestion metrics
            if (
                "summary" in benchmark_metrics
                and "ingestion" in benchmark_metrics["summary"]
            ):
                ingestion = benchmark_metrics["summary"]["ingestion"]
                wandb.log(
                    {
                        "ingestion/avg_duration_s": ingestion.get(
                            "avg_duration_seconds", 0
                        ),
                        "ingestion/p50_duration_s": ingestion.get(
                            "p50_duration_seconds", 0
                        ),
                        "ingestion/p95_duration_s": ingestion.get(
                            "p95_duration_seconds", 0
                        ),
                        "ingestion/p99_duration_s": ingestion.get(
                            "p99_duration_seconds", 0
                        ),
                        "ingestion/avg_throughput_mbs": ingestion.get(
                            "avg_throughput_mb_s", 0
                        ),
                        "ingestion/peak_memory_mb": ingestion.get("peak_memory_mb", 0),
                        "ingestion/total_runs": ingestion.get("total_runs", 0),
                    }
                )

            # Log retrieval metrics
            if (
                "summary" in benchmark_metrics
                and "retrieval" in benchmark_metrics["summary"]
            ):
                retrieval = benchmark_metrics["summary"]["retrieval"]
                wandb.log(
                    {
                        "retrieval/avg_latency_ms": retrieval.get("avg_latency_ms", 0),
                        "retrieval/p50_latency_ms": retrieval.get("p50_latency_ms", 0),
                        "retrieval/p95_latency_ms": retrieval.get("p95_latency_ms", 0),
                        "retrieval/p99_latency_ms": retrieval.get("p99_latency_ms", 0),
                        "retrieval/avg_score": retrieval.get("avg_score", 0),
                        "retrieval/avg_memory_mb": retrieval.get("avg_memory_mb", 0),
                        "retrieval/total_runs": retrieval.get("total_runs", 0),
                    }
                )

            print("Benchmark results logged to W&B")
        except Exception as e:
            print(f"Failed to log benchmark results to W&B: {e}")

    def finish(self):
        """Close the active W&B run if one exists."""
        if self.wandb_enabled and self.wandb_run:
            try:
                import wandb

                wandb.finish()
                print("W&B run finished")
            except Exception as e:
                print(f"Failed to finish W&B run: {e}")


# Singleton instance
_observability_instance: Optional[ObservabilityManager] = None


def get_observability_manager() -> ObservabilityManager:
    """Return the shared observability manager."""
    global _observability_instance
    if _observability_instance is None:
        _observability_instance = ObservabilityManager()
    return _observability_instance
