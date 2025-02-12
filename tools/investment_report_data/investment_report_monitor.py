"""Monitor for new Yuanta research reports."""

import asyncio
import json
import logging
import os
from datetime import datetime, time, timedelta
from typing import Dict, List, Optional, Set

import aiohttp

# Configure paths
BASE_DIR = "/Users/jeffyang/Desktop/TonyStock"
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads", "reports")
FILE_IDS_DIR = os.path.join(BASE_DIR, "downloads", "file_ids")

# Ensure directories exist
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(FILE_IDS_DIR, exist_ok=True)

# Configure logging
log_file = os.path.join(FILE_IDS_DIR, "report_monitor.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class ReportMonitor:
    """Monitor and download research reports from Yuanta consulting.

    This class handles scanning for new reports, tracking known report IDs,
    and downloading newly discovered reports. It maintains a persistent record
    of known report IDs and manages the download process.
    """

    def __init__(self):
        """Initialize the ReportMonitor.

        Sets up the data file path for storing known report IDs, configures
        the base URL for downloading reports, and initializes the tracking
        of known report IDs.
        """
        self.data_file = os.path.join(FILE_IDS_DIR, "reports_data.json")
        self.base_url = (
            "https://research.yuanta-consulting.com.tw/temp/ProductionYT/{file_id}.pdf"
        )
        self.known_ids: Dict[str, List[int]] = {}  # date -> list of IDs
        self.load_known_ids()

    def load_known_ids(self):
        """Load known report IDs from file."""
        if os.path.exists(self.data_file):
            with open(self.data_file, "r") as f:
                self.known_ids = json.load(f)
        logger.info(
            f"Loaded {sum(len(ids) for ids in self.known_ids.values())} known report IDs"
        )

    def save_known_ids(self):
        """Save known report IDs to file."""
        with open(self.data_file, "w") as f:
            json.dump(self.known_ids, f, indent=2)
        logger.info("Saved report IDs to file")

    async def check_report_exists(self, file_id: int) -> bool:
        """Check if a report ID exists by making a HEAD request."""
        url = self.base_url.format(file_id=file_id)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.head(url) as response:
                    return response.status == 200
        except Exception as e:
            logger.debug(f"Error checking {file_id}: {str(e)}")
            return False

    async def scan_range(self, start_id: int, end_id: int) -> Set[int]:
        """Scan a range of IDs for valid reports."""
        tasks = []
        for file_id in range(start_id, end_id + 1):
            tasks.append(self.check_report_exists(file_id))

        results = await asyncio.gather(*tasks)
        valid_ids = {start_id + i for i, exists in enumerate(results) if exists}
        return valid_ids

    def get_date_key(self) -> str:
        """Get today's date key in YYYY-MM-DD format."""
        return datetime.now().strftime("%Y-%m-%d")

    def get_latest_date_from_downloads(self) -> Optional[str]:
        """Get the latest date from DOWNLOAD_DIR in YYYY-MM-DD format."""
        if not os.path.exists(DOWNLOAD_DIR):
            return None

        try:
            # Get all directories and filter for valid dates
            valid_dates = [
                d
                for d in os.listdir(DOWNLOAD_DIR)
                if os.path.isdir(os.path.join(DOWNLOAD_DIR, d))
                and datetime.strptime(d, "%Y-%m-%d")
            ]
            return max(valid_dates) if valid_dates else None
        except ValueError:
            return None

    def get_yesterday_key(self) -> str:
        """Get yesterday's date key in YYYY-MM-DD format."""
        yesterday = datetime.now() - timedelta(days=1)
        return yesterday.strftime("%Y-%m-%d")

    def get_max_id_for_date(self, date_key: str) -> Optional[int]:
        """Get the maximum ID for a given date."""
        if date_key in self.known_ids and self.known_ids[date_key]:
            return max(self.known_ids[date_key])
        return None

    async def scan_for_reports(self):
        """Scan for reports in a single run using a dynamic window around the latest known ID."""
        date_key = self.get_date_key()
        latest_date = self.get_latest_date_from_downloads()
        logger.info(f"Starting daily scan for {date_key}")

        # Get reference ID from latest date or known IDs
        reference_id = None
        if latest_date and latest_date in self.known_ids:
            reference_id = max(self.known_ids[latest_date])
            logger.info(
                f"Using reference ID from latest date {latest_date}: {reference_id}"
            )
        else:
            # Try to find the most recent max ID from known IDs
            sorted_dates = sorted(self.known_ids.keys(), reverse=True)
            for prev_date in sorted_dates:
                if self.known_ids[prev_date]:
                    reference_id = max(self.known_ids[prev_date])
                    logger.info(
                        f"Using reference ID from previous date {prev_date}: {reference_id}"
                    )
                    break

        # Use base ID if no reference found
        if reference_id is None:
            reference_id = 89270
            logger.info(f"No previous reports found, using base ID: {reference_id}")

        # Initialize new day's entry and scanning parameters
        if date_key not in self.known_ids:
            self.known_ids[date_key] = []

        max_distance = 100
        forward_window = reference_id
        backward_window = reference_id
        forward_limit = reference_id + max_distance
        backward_limit = max(reference_id - max_distance, 0)
        found_reports = False

        # Scan until we hit the limits
        while forward_window <= forward_limit or backward_window >= backward_limit:
            tasks = []
            if forward_window <= forward_limit:
                tasks.append(self.check_report_exists(forward_window))
            if backward_window >= backward_limit:
                tasks.append(self.check_report_exists(backward_window))

            if not tasks:
                break

            results = await asyncio.gather(*tasks)
            ids_to_check = [
                id
                for id, exists in zip(
                    [fw for fw in [forward_window] if fw <= forward_limit]
                    + [bw for bw in [backward_window] if bw >= backward_limit],
                    results,
                )
                if exists
            ]

            # Process found IDs
            for file_id in ids_to_check:
                if not any(file_id in ids for ids in self.known_ids.values()):
                    found_reports = True
                    logger.info(f"Found new report {file_id}")
                    self.known_ids[date_key].append(file_id)
                    self.save_known_ids()
                    await self.download_reports({file_id})

            forward_window += 1
            backward_window -= 1
            await asyncio.sleep(0.1)

        if not found_reports:
            logger.info("No new reports found in today's scan")

        logger.info(f"Completed daily scan for {date_key}")
        # Log statistics
        logger.info(f"Started from reference ID: {reference_id}")
        logger.info(f"Scanned forward up to ID {min(forward_window, forward_limit)}")
        logger.info(
            f"Scanned backward down to ID {max(backward_window, backward_limit)}"
        )
        logger.info(
            f"Total known reports: {sum(len(ids) for ids in self.known_ids.values())}"
        )
        logger.info(
            f"Scanning limits were: forward={forward_limit}, backward={backward_limit}"
        )

    async def download_reports(self, report_ids: Set[int]):
        """Download newly found reports using direct PDF URLs."""
        date_key = self.get_date_key()
        download_dir = os.path.join(DOWNLOAD_DIR, date_key)
        os.makedirs(download_dir, exist_ok=True)

        async with aiohttp.ClientSession() as session:
            for file_id in report_ids:
                url = self.base_url.format(file_id=file_id)
                try:
                    async with session.get(url) as response:
                        if response.status == 200:
                            # Save with ID
                            filename = f"{file_id}.pdf"
                            path = os.path.join(download_dir, filename)

                            # Save the PDF content
                            content = await response.read()
                            with open(path, "wb") as f:
                                f.write(content)

                            logger.info(f"Downloaded report {file_id} to {path}")
                        else:
                            logger.error(
                                f"Failed to download report {file_id}: HTTP {response.status}"
                            )
                except Exception as e:
                    logger.error(f"Error downloading report {file_id}: {str(e)}")

        logger.info(f"Completed downloading {len(report_ids)} reports")


async def wait_until_next_run(run_time: time):
    """Wait until the next run time."""
    now = datetime.now()
    target = datetime.combine(now.date(), run_time)

    # If today's run time has passed, wait for tomorrow
    if now.time() >= run_time:
        target += timedelta(days=1)

    wait_seconds = (target - now).total_seconds()
    logger.info(f"Waiting {wait_seconds/3600:.2f} hours until next run at {target}")
    await asyncio.sleep(wait_seconds)


async def main():
    """Execute the report monitoring process.

    Initializes the monitor and performs a scan for new reports. Can be
    configured to run on a schedule or as a one-time scan.
    """
    monitor = ReportMonitor()
    await monitor.scan_for_reports()
    # Run at 8:00 PM every day
    # run_time = time(20, 0)  # 24-hour format

    # monitor = ReportMonitor()
    # try:
    #     while True:
    #         await wait_until_next_run(run_time)
    #         await monitor.scan_for_reports()
    # except KeyboardInterrupt:
    #     logger.info("Monitoring stopped by user")
    # except Exception as e:
    #     logger.error(f"Error during monitoring: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
