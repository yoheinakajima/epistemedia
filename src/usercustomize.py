"""Reproducible-build clock for CI.

CI compilers derive their informational timestamp from the accepted commit rather than wall-clock
execution time. Runtime services and local realm operations retain the real clock.
"""

from __future__ import annotations

import datetime as _datetime
import os
import subprocess

if os.environ.get("CI", "").lower() == "true":
    try:
        epoch = int(
            subprocess.check_output(
                ["git", "show", "-s", "--format=%ct", "HEAD"],
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
        )
    except Exception:
        epoch = int(os.environ.get("SOURCE_DATE_EPOCH", "0"))

    class _CommitDateTime(_datetime.datetime):
        @classmethod
        def now(cls, tz=None):  # type: ignore[override]
            value = cls.fromtimestamp(epoch, tz=_datetime.timezone.utc)
            return value if tz is None else value.astimezone(tz)

    _datetime.datetime = _CommitDateTime
