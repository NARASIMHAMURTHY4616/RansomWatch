"""
Process monitoring module for RansomWatch.
Uses psutil to inspect and record process telemetry safely without privilege escalation or process termination.
"""

import os
import time
import logging
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, List, Dict, Any
import psutil

from config.settings import settings

logger = logging.getLogger("RansomWatch.ProcessMonitor")


@dataclass
class ProcessInfo:
    """Process snapshot containing identification and resource usage."""
    pid: int
    name: str
    exe: Optional[str]
    cmdline: List[str]
    cpu_percent: float
    memory_percent: float
    status: str
    create_time: float
    timestamp: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ProcessMonitor:
    """Safely captures process information related to filesystem events."""

    def __init__(self, watch_dir: Path | None = None):
        self.watch_dir = (watch_dir or settings.TEST_DATA_DIR).resolve()

    def get_process_info(self, pid: int) -> Optional[ProcessInfo]:
        """Retrieve telemetry for a specific PID."""
        try:
            p = psutil.Process(pid)
            with p.oneshot():
                name = p.name()
                try:
                    exe = p.exe()
                except (psutil.AccessDenied, psutil.ZombieProcess):
                    exe = None
                try:
                    cmdline = p.cmdline()
                except (psutil.AccessDenied, psutil.ZombieProcess):
                    cmdline = []
                try:
                    cpu = p.cpu_percent(interval=None)
                except (psutil.AccessDenied, psutil.ZombieProcess):
                    cpu = 0.0
                try:
                    mem = p.memory_percent()
                except (psutil.AccessDenied, psutil.ZombieProcess):
                    mem = 0.0
                try:
                    status = p.status()
                except (psutil.AccessDenied, psutil.ZombieProcess):
                    status = "unknown"
                try:
                    create_time = p.create_time()
                except (psutil.AccessDenied, psutil.ZombieProcess):
                    create_time = 0.0

            return ProcessInfo(
                pid=pid,
                name=name,
                exe=exe,
                cmdline=cmdline,
                cpu_percent=round(cpu, 2),
                memory_percent=round(mem, 2),
                status=status,
                create_time=create_time,
                timestamp=time.time(),
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return None
        except Exception as e:
            logger.debug(f"Error querying process {pid}: {e}")
            return None

    def find_active_file_accessor(self) -> Optional[ProcessInfo]:
        """
        Attempt to identify the process interacting with test_data/ or simulator.
        Scans open files or command line parameters of running processes.
        """
        current_pid = os.getpid()
        watch_str = str(self.watch_dir)

        # 1. Search for processes having open files inside watch_dir
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.pid == current_pid:
                    continue
                # Check command line for attack_simulator or simulator
                cmdline = proc.info.get('cmdline') or []
                cmd_str = " ".join(cmdline)
                if "attack_simulator" in cmd_str or "simulator.py" in cmd_str:
                    return self.get_process_info(proc.pid)

                # Check open files if permissions allow
                try:
                    open_files = proc.open_files()
                    for f in open_files:
                        if watch_str in f.path:
                            return self.get_process_info(proc.pid)
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    pass
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # 2. Fallback: Return current process telemetry if no external simulator is found
        return self.get_process_info(current_pid)

    def get_top_cpu_processes(self, limit: int = 5) -> List[ProcessInfo]:
        """Return top processes sorted by CPU utilization."""
        processes = []
        for proc in psutil.process_iter(['pid']):
            try:
                info = self.get_process_info(proc.pid)
                if info:
                    processes.append(info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        processes.sort(key=lambda x: x.cpu_percent, reverse=True)
        return processes[:limit]
