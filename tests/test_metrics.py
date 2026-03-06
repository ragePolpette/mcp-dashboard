"""Tests for dashboard metrics computation."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.main import _compute_metrics  # noqa: E402


def test_context_trend_uses_only_context_retrieval_events():
    now = datetime.now(timezone.utc)
    entries = [
        {
            "timestamp": (now - timedelta(minutes=1)).isoformat(),
            "event": "context.retrieved",
            "level": "INFO",
            "fields": {},
        },
        {
            "timestamp": (now - timedelta(minutes=1)).isoformat(),
            "event": "log.python",
            "level": "INFO",
            "fields": {},
        },
        {
            "timestamp": (now - timedelta(minutes=3)).isoformat(),
            "event": "context.retrieved",
            "level": "INFO",
            "fields": {},
        },
    ]

    metrics = _compute_metrics(entries)

    assert sum(metrics["activity_series"]) == 3
    assert sum(metrics["context_retrieval_series"]) == 2
    assert metrics["context_retrieved_today"] == 2
