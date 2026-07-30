"""Keeps the most recent analyses in memory, keyed by request_id, so the
Agent Trace View, Citations Panel, and PDF export endpoints can look up
a previous analysis without re-running the whole LangGraph pipeline.

In production this would be a Redis/Postgres table instead of an
in-process dict, but the interface stays the same.
"""

from collections import OrderedDict
from app.core.logging_config import get_logger, log_event

logger = get_logger(__name__)

_MAX_CACHE_SIZE = 200
_cache: "OrderedDict[str, dict]" = OrderedDict()


def store_analysis(request_id: str, analysis: dict) -> None:
    _cache[request_id] = analysis
    if len(_cache) > _MAX_CACHE_SIZE:
        oldest = next(iter(_cache))
        _cache.pop(oldest)
    log_event(logger, "analysis_cached", request_id=request_id, cache_size=len(_cache))


def get_analysis(request_id: str) -> dict | None:
    result = _cache.get(request_id)
    log_event(logger, "analysis_cache_lookup", request_id=request_id, found=result is not None)
    return result


def list_recent(limit: int = 10) -> list[dict]:
    items = list(_cache.values())[-limit:]
    log_event(logger, "analysis_cache_list", returned=len(items))
    return list(reversed(items))
