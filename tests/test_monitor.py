"""
Unit tests for watchdog file monitoring and process monitoring.
"""

import time
import queue
from pathlib import Path
from monitor.file_monitor import FileEvent, RansomWatchEventHandler, FileMonitor
from monitor.process_monitor import ProcessMonitor


def test_file_event_creation():
    """Verify FileEvent dataclass representation and dictionary serialization."""
    event = FileEvent(
        timestamp=time.time(),
        event_type="MODIFY",
        src_path="/tmp/test_data/file.txt",
        dest_path=None,
        filename="file.txt",
        directory="/tmp/test_data",
        is_directory=False,
    )
    d = event.to_dict()
    assert d["event_type"] == "MODIFY"
    assert d["filename"] == "file.txt"
    assert d["directory"] == "/tmp/test_data"
    assert not d["is_directory"]


def test_event_handler_enqueuing():
    """Verify RansomWatchEventHandler correctly formats and queues events."""
    event_q = queue.Queue()
    captured_callbacks = []

    def test_cb(ev):
        captured_callbacks.append(ev)

    handler = RansomWatchEventHandler(event_queue=event_q, callbacks=[test_cb])

    # Simulate a file move/rename event
    handler._process_event(
        event_type="RENAME",
        src_path="/tmp/test_data/invoice.txt",
        dest_path="/tmp/test_data/invoice.txt.locked",
        is_directory=False,
    )

    assert not event_q.empty()
    queued_event = event_q.get()
    assert queued_event.event_type == "RENAME"
    assert queued_event.filename == "invoice.txt"
    assert len(captured_callbacks) == 1
    assert captured_callbacks[0].dest_path == "/tmp/test_data/invoice.txt.locked"


def test_process_monitor_current():
    """Verify ProcessMonitor can safely query process telemetry without root privileges."""
    pm = ProcessMonitor()
    info = pm.find_active_file_accessor()
    assert info is not None
    assert info.pid > 0
    assert isinstance(info.name, str)
    assert 0.0 <= info.cpu_percent <= 100.0
    assert 0.0 <= info.memory_percent <= 100.0
