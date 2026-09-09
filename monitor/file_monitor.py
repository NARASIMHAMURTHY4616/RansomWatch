"""
Filesystem monitor for RansomWatch.
Uses watchdog to capture filesystem activity strictly within test_data/ in real time.
"""

import os
import time
import queue
import logging
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, Callable, List
from watchdog.observers import Observer
from watchdog.events import (
    FileSystemEventHandler,
    FileCreatedEvent,
    FileModifiedEvent,
    FileMovedEvent,
    FileDeletedEvent,
    FileSystemEvent,
)

from config.settings import settings

logger = logging.getLogger("RansomWatch.FileMonitor")


@dataclass
class FileEvent:
    """Represents an intercepted filesystem event."""
    timestamp: float
    event_type: str  # CREATE, MODIFY, RENAME, DELETE
    src_path: str
    dest_path: Optional[str]
    filename: str
    directory: str
    is_directory: bool

    def to_dict(self) -> dict:
        return asdict(self)


class RansomWatchEventHandler(FileSystemEventHandler):
    """Watches and enqueues filesystem events strictly within monitored path."""

    def __init__(self, event_queue: queue.Queue, callbacks: List[Callable[[FileEvent], None]]):
        super().__init__()
        self.event_queue = event_queue
        self.callbacks = callbacks

    def _process_event(
        self,
        event_type: str,
        src_path: str,
        dest_path: Optional[str] = None,
        is_directory: bool = False,
    ) -> None:
        # Ignore .gitkeep or hidden IDE tracking files
        src_obj = Path(src_path)
        if src_obj.name.startswith(".git") or src_obj.name.endswith(".tmp_test"):
            return

        filename = src_obj.name
        directory = str(src_obj.parent)

        file_event = FileEvent(
            timestamp=time.time(),
            event_type=event_type,
            src_path=src_path,
            dest_path=dest_path,
            filename=filename,
            directory=directory,
            is_directory=is_directory,
        )

        self.event_queue.put(file_event)

        for callback in self.callbacks:
            try:
                callback(file_event)
            except Exception as e:
                logger.error(f"Error executing callback for event {file_event}: {e}")

    def on_created(self, event: FileSystemEvent) -> None:
        self._process_event(
            event_type="CREATE",
            src_path=event.src_path,
            is_directory=event.is_directory,
        )

    def on_modified(self, event: FileSystemEvent) -> None:
        self._process_event(
            event_type="MODIFY",
            src_path=event.src_path,
            is_directory=event.is_directory,
        )

    def on_moved(self, event: FileMovedEvent) -> None:
        self._process_event(
            event_type="RENAME",
            src_path=event.src_path,
            dest_path=event.dest_path,
            is_directory=event.is_directory,
        )

    def on_deleted(self, event: FileSystemEvent) -> None:
        self._process_event(
            event_type="DELETE",
            src_path=event.src_path,
            is_directory=event.is_directory,
        )


class FileMonitor:
    """Continuous watchdog-based filesystem monitoring service for test_data/."""

    def __init__(self, watch_dir: Path | None = None):
        self.watch_dir = (watch_dir or settings.TEST_DATA_DIR).resolve()
        self.watch_dir.mkdir(parents=True, exist_ok=True)
        self.event_queue: queue.Queue[FileEvent] = queue.Queue()
        self.callbacks: List[Callable[[FileEvent], None]] = []
        self._observer: Optional[Observer] = None
        self._running: bool = False
        self._total_events: int = 0

    def register_callback(self, callback: Callable[[FileEvent], None]) -> None:
        """Register a subscriber callback invoked on every filesystem event."""
        self.callbacks.append(callback)

    def start(self) -> None:
        """Start the watchdog observer."""
        if self._running:
            logger.warning("FileMonitor observer is already running.")
            return

        event_handler = RansomWatchEventHandler(
            event_queue=self.event_queue,
            callbacks=self.callbacks,
        )
        self._observer = Observer()
        self._observer.schedule(event_handler, str(self.watch_dir), recursive=True)
        self._observer.daemon = True
        self._observer.start()
        self._running = True
        logger.info(f"FileMonitor started watching: {self.watch_dir}")

    def stop(self) -> None:
        """Stop the watchdog observer."""
        if not self._running:
            return

        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=2.0)
            self._observer = None

        self._running = False
        logger.info("FileMonitor stopped.")

    def is_running(self) -> bool:
        return self._running and (self._observer is not None and self._observer.is_alive())

    def get_events(self, max_items: Optional[int] = None) -> List[FileEvent]:
        """Drain and return queued events up to max_items (non-blocking)."""
        events = []
        while not self.event_queue.empty():
            try:
                event = self.event_queue.get_nowait()
                events.append(event)
                self._total_events += 1
                if max_items and len(events) >= max_items:
                    break
            except queue.Empty:
                break
        return events

    @property
    def total_events_recorded(self) -> int:
        return self._total_events
