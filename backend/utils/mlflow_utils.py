
import mlflow
import os
import time
from contextlib import contextmanager
from functools import wraps
from typing import Any, Optional, Dict
from config import settings

class MLFlowService:
    def __init__(self, experiment_name: str = "NexusLearn_Experiments"):
        self.experiment_name = experiment_name
        self.tracking_uri = "file:./mlruns" # Local logging for now
        
        mlflow.set_tracking_uri(self.tracking_uri)
        mlflow.set_experiment(self.experiment_name)
        # Enable system metrics logging (CPU, RAM, etc.) if psutil is available
        try:
            import psutil
            mlflow.enable_system_metrics_logging()
        except ImportError:
            print("pustil not installed. System metrics logging disabled.")
        except Exception:
             # Might fail if not supported in this version/environment, safe to ignore
            pass

    def log_run(self, run_name: str, parameters: Dict[str, Any] = None, metrics: Dict[str, Any] = None, tags: Dict[str, str] = None):
        """
        Log a generic run to MLflow.
        """
        with mlflow.start_run(run_name=run_name):
            if parameters:
                mlflow.log_params(parameters)
            if metrics:
                mlflow.log_metrics(metrics)
            if tags:
                mlflow.set_tags(tags)

    @contextmanager
    def track_run(self, run_name: str, tags: Dict[str, str] = None, nested: bool = True):
        """
        Context manager to track a run with detailed logging capabilities.
        Suports nested runs automatically.
        """
        # nested=True allows this run to be created even if another run is active
        with mlflow.start_run(run_name=run_name, nested=nested) as run:
            if tags:
                mlflow.set_tags(tags)
            
            start_time = time.time()
            status = "success"
            
            try:
                yield run
            except Exception as e:
                status = "failed"
                mlflow.log_param("error_type", type(e).__name__)
                mlflow.log_param("error_message", str(e))
                raise e
            finally:
                duration = time.time() - start_time
                mlflow.log_metric("latency_seconds", duration)
                mlflow.log_param("status", status)

    def track_latency(self, run_name_prefix: str):
        """
        Decorator to track execution time of a function.
        """
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Ensure nested=True is used here as well
                with self.track_run(f"{run_name_prefix}_{func.__name__}", nested=True):
                     # Try to capture relevant inputs if possible (simplified)
                    if kwargs.get('plan_request'):
                        mlflow.log_param("exam_type", getattr(kwargs['plan_request'], 'exam_type', 'unknown'))
                    return await func(*args, **kwargs)
            return wrapper
        return decorator

mlflow_service = MLFlowService()
