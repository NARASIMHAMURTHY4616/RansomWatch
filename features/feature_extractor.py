"""
Behavioral Feature Extractor for RansomWatch.
Calculates filesystem event rates and burst metrics over a sliding time window.
"""

import time
from collections import deque
from typing import List, Dict, Any, Optional
import pandas as pd

from config.settings import settings
from monitor.file_monitor import FileEvent


class BehavioralFeatureExtractor:
    """Extracts real-time behavioral features using a short sliding time window."""

    def __init__(self, window_seconds: float = 5.0, subwindow_seconds: float = 1.0):
        self.window_seconds = window_seconds
        self.subwindow_seconds = subwindow_seconds
        self.events_buffer: deque[FileEvent] = deque()

    def add_event(self, event: FileEvent) -> None:
        """Add a single event to the sliding window buffer."""
        self.events_buffer.append(event)
        self._prune_old_events(current_time=event.timestamp)

    def add_events(self, events: List[FileEvent]) -> None:
        """Add multiple events to the sliding window buffer."""
        now = time.time()
        for event in events:
            self.events_buffer.append(event)
        self._prune_old_events(current_time=now)

    def _prune_old_events(self, current_time: Optional[float] = None) -> None:
        """Discard events that fall outside the current sliding window [now - window_seconds, now]."""
        now = current_time if current_time is not None else time.time()
        cutoff = now - self.window_seconds
        while self.events_buffer and self.events_buffer[0].timestamp < cutoff:
            self.events_buffer.popleft()

    def calculate_burst(self, events: List[FileEvent], now: float) -> float:
        """
        Calculate maximum operations observed within any 1-second sub-interval in the window.
        Uses 1-second rolling buckets to measure burst intensity.
        """
        if not events:
            return 0.0

        # Sub-window bins: check 1s sliding windows
        timestamps = [e.timestamp for e in events]
        max_ops_in_1s = 0
        left = 0
        for right in range(len(timestamps)):
            while timestamps[right] - timestamps[left] > self.subwindow_seconds:
                left += 1
            current_count = right - left + 1
            if current_count > max_ops_in_1s:
                max_ops_in_1s = current_count

        return float(max_ops_in_1s)

    def extract_features(self, current_time: Optional[float] = None) -> Dict[str, Any]:
        """
        Compute behavioral feature rates for the current active sliding window.
        Returns a dictionary with keys matching settings.FEATURE_NAMES.
        """
        now = current_time if current_time is not None else time.time()
        self._prune_old_events(current_time=now)

        events = list(self.events_buffer)
        window = max(self.window_seconds, 1.0)

        create_count = 0
        modify_count = 0
        rename_count = 0
        delete_count = 0
        directories_set = set()

        for ev in events:
            ev_type = ev.event_type.upper()
            if ev_type == "CREATE":
                create_count += 1
            elif ev_type == "MODIFY":
                modify_count += 1
            elif ev_type in ("RENAME", "MOVE"):
                rename_count += 1
            elif ev_type == "DELETE":
                delete_count += 1

            if ev.directory:
                directories_set.add(ev.directory)

        total_ops = len(events)
        burst = self.calculate_burst(events, now)

        features = {
            "create_rate": round(create_count / window, 3),
            "modified_rate": round(modify_count / window, 3),
            "rename_rate": round(rename_count / window, 3),
            "delete_rate": round(delete_count / window, 3),
            "operations_rate": round(total_ops / window, 3),
            "directories_affected": len(directories_set),
            "activity_burst": round(burst, 3),
        }
        return features

    def to_dataframe(self, features: Dict[str, Any]) -> pd.DataFrame:
        """Convert a feature dict to a single-row DataFrame ordered as required by the ML model."""
        ordered = {k: [features.get(k, 0.0)] for k in settings.FEATURE_NAMES}
        return pd.DataFrame(ordered)

    def clear(self) -> None:
        """Reset internal buffer."""
        self.events_buffer.clear()
