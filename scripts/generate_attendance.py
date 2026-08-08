"""
Odoo Attendance Automation Script

Bulk generates attendance records for all employees in the HR module
using Odoo's XML-RPC API with batch operations for optimal performance.
"""

import random
import time
from dataclasses import dataclass
from datetime import datetime, timedelta

from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from odoo_rpc_utils import OdooClient, console, setup_logging

# Setup logging
log = setup_logging("odoo-attendance")


@dataclass
class AttendanceRecord:
    """Represents a single attendance record for an employee."""
    employee_id: int
    check_in: datetime
    check_out: datetime
    break_out: datetime
    break_in: datetime


def generate_random_attendance(
    employee_id: int, target_date: datetime
) -> AttendanceRecord:
    """
    Generates realistic attendance data for a given date.
    
    Args:
        employee_id: The Odoo employee ID
        target_date: The date to generate attendance for
        
    Returns:
        AttendanceRecord with randomized but realistic times
    """
    check_in = target_date.replace(
        hour=8, minute=max(0, min(59, int(random.gauss(30, 15)))), second=0
    )
    break_out = target_date.replace(hour=12, minute=random.randint(0, 15), second=0)
    break_in = target_date.replace(hour=13, minute=random.randint(0, 15), second=0)
    check_out = target_date.replace(hour=17, minute=0, second=0) + timedelta(
        minutes=random.randint(0, 120)
    )
    return AttendanceRecord(employee_id, check_in, check_out, break_out, break_in)


class AttendanceClient(OdooClient):
    """Client for creating attendance records via XML-RPC."""

    def __init__(self, timezone_offset: int = 8, **kwargs):
        """
        Initialize AttendanceClient.
        
        Args:
            timezone_offset: Hours offset from UTC (default: 8 for PHT)
            **kwargs: Additional arguments passed to OdooClient
        """
        super().__init__(**kwargs)
        self.timezone_offset = timezone_offset

    def _to_utc_str(self, dt: datetime) -> str:
        """Convert datetime to UTC string for Odoo."""
        fmt = "%Y-%m-%d %H:%M:%S"
        return (dt - timedelta(hours=self.timezone_offset)).strftime(fmt)

    def _record_to_vals(self, record: AttendanceRecord) -> dict:
        """Convert an AttendanceRecord to Odoo values dict."""
        return {
            "employee_id": record.employee_id,
            "check_in": self._to_utc_str(record.check_in),
            "check_out": self._to_utc_str(record.check_out),
            "break_out": self._to_utc_str(record.break_out),
            "break_in": self._to_utc_str(record.break_in),
        }

    def create_attendance_batch(
        self, records: list[AttendanceRecord]
    ) -> tuple[list[int], float]:
        """
        Create multiple attendance records in a single batch call.
        
        Odoo 12+ supports batch creation by passing a list of dictionaries
        to the create() method. This dramatically reduces network overhead.
        
        Returns:
            tuple: (list of created IDs, duration in seconds)
        """
        vals_list = [self._record_to_vals(record) for record in records]

        start_time = time.perf_counter()
        try:
            created_ids = self.odoo.env["hr.attendance"].create(vals_list)
            duration = time.perf_counter() - start_time
            return created_ids, duration
        except Exception as e:
            log.warning(f"Batch failed, falling back to individual creates: {e}")
            # Fallback: create records one by one
            created_ids = []
            for vals in vals_list:
                try:
                    record_id = self.odoo.env["hr.attendance"].create(vals)
                    created_ids.append(record_id)
                except Exception as inner_e:
                    log.debug(f"Individual create failed: {inner_e}")
            duration = time.perf_counter() - start_time
            return created_ids, duration

    def create_attendance_batches(
        self,
        records: list[AttendanceRecord],
        batch_size: int = 100,
        progress=None,
        task=None,
    ) -> tuple[int, float]:
        """
        Create records in batches with progress tracking.
        
        Args:
            records: List of AttendanceRecord to create
            batch_size: Number of records per batch
            progress: Rich Progress object for updates
            task: Rich task ID for progress updates
            
        Returns:
            tuple: (total records created, total server time)
        """
        total_created = 0
        total_time = 0.0

        for i in range(0, len(records), batch_size):
            batch = records[i : i + batch_size]
            created_ids, duration = self.create_attendance_batch(batch)

            if created_ids:
                total_created += len(created_ids)
                total_time += duration

            if progress and task is not None:
                progress.advance(task, len(batch))

        return total_created, total_time

    def get_all_employees(self) -> list[int]:
        """Fetch all employee IDs from the database."""
        Employee = self.odoo.env["hr.employee"]
        return Employee.search([])


def main():
    """Main entry point for the attendance automation script."""
    script_start = time.perf_counter()

    # Parse configuration from environment
    batch_size = int(os.getenv("BATCH_SIZE", "100"))
    start_date_str = os.getenv("START_DATE", "2025-01-01")
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    end_date = datetime.now()
    timezone_offset = int(os.getenv("TIMEZONE_OFFSET", "8"))

    try:
        # Initialize client with proxy support from environment
        client = AttendanceClient.from_env(timezone_offset=timezone_offset, logger=log)
        client.login()

        # Fetch ALL employees from the database
        console.print("[cyan]Fetching all employees...[/cyan]")
        employee_ids = client.get_all_employees()
        console.print(f"[green]Found {len(employee_ids)} employees[/green]")

        # Prepare Workdays
        workdays = []
        curr = start_date
        while curr <= end_date:
            if curr.weekday() < 5:
                workdays.append(curr)
            curr += timedelta(days=1)

        # Generate attendance records for ALL employees
        console.print("[cyan]Generating attendance records...[/cyan]")
        records = []
        for emp_id in employee_ids:
            for day in workdays:
                records.append(generate_random_attendance(emp_id, day))

        total_records = len(records)
        console.print(
            f"[green]Generated {total_records} records "
            f"({len(employee_ids)} employees × {len(workdays)} workdays)[/green]"
        )

        # --- BATCH UPLOAD ---
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(
                f"[cyan]Uploading {total_records} records in batches of {batch_size}...",
                total=total_records,
            )

            records_created, total_api_time = client.create_attendance_batches(
                records, batch_size=batch_size, progress=progress, task=task
            )

        # --- METRICS ---
        script_end = time.perf_counter()
        total_runtime = script_end - script_start

        table = Table(title="⚡ Execution Metrics", title_style="bold yellow")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")
        table.add_row("Employees", str(len(employee_ids)))
        table.add_row("Workdays", str(len(workdays)))
        table.add_row("Batch Size", str(batch_size))
        table.add_row(
            "API Calls", str((total_records + batch_size - 1) // batch_size)
        )
        table.add_row("Records Created", str(records_created))
        table.add_row("Wall Clock Time", f"{total_runtime:.2f}s")
        table.add_row("Server Time", f"{total_api_time:.2f}s")
        table.add_row(
            "Records/Second",
            f"{records_created / total_runtime:.1f}" if total_runtime > 0 else "N/A",
        )

        console.print("\n")
        console.print(table)

    except Exception as e:
        log.critical(f"Fatal error: {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
