import functools
import inspect
import logging
import sys
import time
from typing import Any, Callable, Dict, List

# Configure structured root logger
LOG_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("DocIntelligence")

# In-memory execution timing log for easy API retrieval/diagnostics
EXECUTION_METRICS: List[Dict[str, Any]] = []


def get_logger(name: str) -> logging.Logger:
    """Return a child logger for a specific module or agent."""
    return logger.getChild(name)


def timed_agent(agent_name: str):
    """
    Decorator to measure and log latency per agent call (sync and async).
    Fulfills Rule 4 and FR-observability requirements.
    """
    def decorator(func: Callable):
        agent_logger = get_logger(agent_name)

        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.perf_counter()
                status = "SUCCESS"
                error_msg = None
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as ex:
                    status = "FAILED"
                    error_msg = str(ex)
                    raise
                finally:
                    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
                    metric = {
                        "agent": agent_name,
                        "function": func.__name__,
                        "latency_ms": duration_ms,
                        "status": status,
                        "error": error_msg,
                        "timestamp": time.time(),
                    }
                    EXECUTION_METRICS.append(metric)
                    agent_logger.info(
                        f"[AGENT_LATENCY] agent={agent_name} function={func.__name__} "
                        f"latency_ms={duration_ms} status={status}"
                    )
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.perf_counter()
                status = "SUCCESS"
                error_msg = None
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as ex:
                    status = "FAILED"
                    error_msg = str(ex)
                    raise
                finally:
                    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
                    metric = {
                        "agent": agent_name,
                        "function": func.__name__,
                        "latency_ms": duration_ms,
                        "status": status,
                        "error": error_msg,
                        "timestamp": time.time(),
                    }
                    EXECUTION_METRICS.append(metric)
                    agent_logger.info(
                        f"[AGENT_LATENCY] agent={agent_name} function={func.__name__} "
                        f"latency_ms={duration_ms} status={status}"
                    )
            return sync_wrapper

    return decorator
