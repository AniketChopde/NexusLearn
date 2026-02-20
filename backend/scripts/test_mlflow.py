
import sys
import os
import asyncio

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.mlflow_utils import mlflow_service

async def test_mlflow_logging():
    print("Testing MLflow logging...")
    
    # Test manual logging
    mlflow_service.log_run(
        run_name="test_manual_run",
        parameters={"param1": "value1"},
        metrics={"metric1": 1.0}
    )
    print("Manual logging completed.")

    # Test decorator
    @mlflow_service.track_latency("test_decorator")
    async def dummy_function(x):
        await asyncio.sleep(0.1)
        return x * 2

    result = await dummy_function(5)
    print(f"Decorator test result: {result}")
    
    # Check if mlruns directory exists
    if os.path.exists("mlruns"):
        print("SUCCESS: mlruns directory created.")
    else:
        print("FAILURE: mlruns directory not found.")

if __name__ == "__main__":
    asyncio.run(test_mlflow_logging())
