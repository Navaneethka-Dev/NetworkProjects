"""
NetAutomate Pro - Scheduler
Runs periodic backup and device health-check jobs without requiring Celery.
Uses Python's built-in threading and schedule library with a graceful shutdown.

Author: Navaneethraj KA
"""

from __future__ import annotations

import threading
import time
import signal
import sys
from datetime import datetime
from typing import Callable, Dict, List, Optional

try:
    import schedule
    SCHEDULE_AVAILABLE = True
except ImportError:
    SCHEDULE_AVAILABLE = False

from .utils import setup_logging

logger = setup_logging()


class JobResult:
    """Holds the result of a single scheduled job execution."""

    def __init__(self, job_name: str, success: bool, detail: str = ""):
        self.job_name = job_name
        self.success = success
        self.detail = detail
        self.timestamp = datetime.now().isoformat()

    def __repr__(self) -> str:  # pragma: no cover
        status = "OK" if self.success else "FAIL"
        return f"<JobResult [{status}] {self.job_name} @ {self.timestamp}>"


class NetAutomateScheduler:
    """
    Lightweight task scheduler for NetAutomate Pro.

    Wraps the ``schedule`` library (or falls back to a simple
    interval loop) to run recurring backup and health-check jobs.

    Usage::

        from netautomate import NetworkAutomation
        from netautomate.scheduler import NetAutomateScheduler

        na = NetworkAutomation('inventory/devices.yaml')
        sched = NetAutomateScheduler(na)
        sched.schedule_backups(interval_hours=6)
        sched.schedule_health_checks(interval_minutes=15)
        sched.start()          # blocks; Ctrl-C to stop
    """

    def __init__(self, automation, backup_dir: str = "backups"):
        """
        Args:
            automation: A :class:`~netautomate.core.NetworkAutomation` instance.
            backup_dir: Directory where backups will be stored.
        """
        self.automation = automation
        self.backup_dir = backup_dir
        self._stop_event = threading.Event()
        self._history: List[JobResult] = []
        self._lock = threading.Lock()

        if not SCHEDULE_AVAILABLE:
            logger.warning(
                "The 'schedule' library is not installed. "
                "Install it with: pip install schedule"
            )

    # ------------------------------------------------------------------
    # Public scheduling API
    # ------------------------------------------------------------------

    def schedule_backups(self, interval_hours: int = 6) -> "NetAutomateScheduler":
        """Schedule a full-fleet backup every *interval_hours* hours."""
        if not SCHEDULE_AVAILABLE:
            logger.error("Cannot schedule backups: 'schedule' not installed.")
            return self

        schedule.every(interval_hours).hours.do(self._run_backup_job)
        logger.info(
            f"Scheduled all-device backups every {interval_hours} hour(s)."
        )
        return self

    def schedule_health_checks(
        self, interval_minutes: int = 15
    ) -> "NetAutomateScheduler":
        """Schedule a fleet-wide health (ping) check every *interval_minutes* minutes."""
        if not SCHEDULE_AVAILABLE:
            logger.error("Cannot schedule health checks: 'schedule' not installed.")
            return self

        schedule.every(interval_minutes).minutes.do(self._run_health_check_job)
        logger.info(
            f"Scheduled health checks every {interval_minutes} minute(s)."
        )
        return self

    def schedule_custom(
        self,
        job_fn: Callable,
        interval_minutes: int = 60,
        job_name: str = "custom_job",
    ) -> "NetAutomateScheduler":
        """Schedule an arbitrary callable at a fixed interval.

        Args:
            job_fn: Zero-argument callable to run.
            interval_minutes: How often to run.
            job_name: Human-readable name used in logs.
        """
        if not SCHEDULE_AVAILABLE:
            logger.error("Cannot schedule job: 'schedule' not installed.")
            return self

        def _wrapper():
            try:
                job_fn()
                self._record(job_name, success=True)
            except Exception as exc:
                logger.error(f"Custom job '{job_name}' failed: {exc}")
                self._record(job_name, success=False, detail=str(exc))

        schedule.every(interval_minutes).minutes.do(_wrapper)
        logger.info(
            f"Scheduled custom job '{job_name}' every {interval_minutes} minute(s)."
        )
        return self

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self, blocking: bool = True) -> Optional[threading.Thread]:
        """Start the scheduler.

        Args:
            blocking: If ``True`` (default) run in the current thread and
                      block until a SIGINT/SIGTERM is received.
                      If ``False`` start a daemon thread and return it.

        Returns:
            The background thread when ``blocking=False``, else ``None``.
        """
        if not SCHEDULE_AVAILABLE:
            logger.error("Scheduler cannot start: 'schedule' not installed.")
            return None

        logger.info("NetAutomate Scheduler starting…")

        # Register OS signals for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        if blocking:
            self._run_loop()
            return None

        thread = threading.Thread(target=self._run_loop, daemon=True, name="na-scheduler")
        thread.start()
        return thread

    def stop(self) -> None:
        """Signal the scheduler loop to exit."""
        logger.info("Scheduler stop requested.")
        self._stop_event.set()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _run_loop(self) -> None:
        """Main scheduler loop – checks for pending jobs every second."""
        logger.info("Scheduler loop running. Press Ctrl-C to stop.")
        while not self._stop_event.is_set():
            schedule.run_pending()
            time.sleep(1)
        logger.info("Scheduler loop exited.")

    def _signal_handler(self, signum, frame) -> None:  # pragma: no cover
        logger.info(f"Signal {signum} received. Stopping scheduler…")
        self.stop()
        sys.exit(0)

    def _run_backup_job(self) -> None:
        """Execute a full-fleet backup and record results."""
        logger.info("⏰  Scheduled backup job started.")
        try:
            results = self.automation.backup_all_devices()
            ok = sum(1 for r in results if r.get("status") == "success")
            fail = len(results) - ok
            detail = f"{ok} succeeded, {fail} failed"
            self._record("scheduled_backup", success=(fail == 0), detail=detail)
            logger.info(f"Scheduled backup done: {detail}")
        except Exception as exc:
            logger.error(f"Scheduled backup job error: {exc}")
            self._record("scheduled_backup", success=False, detail=str(exc))

    def _run_health_check_job(self) -> None:
        """Ping all devices and log reachability."""
        logger.info("⏰  Health-check job started.")
        results = []
        for device in self.automation.devices:
            hostname = device["hostname"]
            try:
                reachable = self.automation.ping_device(hostname)
                status = "online" if reachable else "offline"
                results.append({"hostname": hostname, "status": status})
                logger.info(f"  {hostname}: {status}")
            except Exception as exc:
                logger.warning(f"  {hostname}: check failed – {exc}")
                results.append({"hostname": hostname, "status": "error", "error": str(exc)})

        online = sum(1 for r in results if r["status"] == "online")
        detail = f"{online}/{len(results)} devices online"
        self._record("health_check", success=True, detail=detail)
        logger.info(f"Health-check done: {detail}")

    def _record(self, job_name: str, success: bool, detail: str = "") -> None:
        with self._lock:
            self._history.append(JobResult(job_name, success, detail))
            # Keep only last 500 records to avoid unbounded memory
            if len(self._history) > 500:
                self._history = self._history[-500:]

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------

    def get_history(self, limit: int = 50) -> List[Dict]:
        """Return the most recent job results as plain dicts."""
        with self._lock:
            records = self._history[-limit:]
        return [
            {
                "job": r.job_name,
                "success": r.success,
                "detail": r.detail,
                "timestamp": r.timestamp,
            }
            for r in reversed(records)
        ]

    def print_history(self, limit: int = 20) -> None:  # pragma: no cover
        """Pretty-print recent job history to stdout."""
        records = self.get_history(limit)
        print(f"\n{'=' * 60}")
        print(f"  Scheduler History (last {limit} entries)")
        print(f"{'=' * 60}")
        for r in records:
            icon = "✅" if r["success"] else "❌"
            print(f"  {icon}  {r['timestamp']}  {r['job']:25s}  {r['detail']}")
        print(f"{'=' * 60}\n")
