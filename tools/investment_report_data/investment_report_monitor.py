"""Monitor and download new Yuanta research reports."""

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
                async with session.head(url, timeout=30) as response:
                    return response.status == 200
        except asyncio.TimeoutError:
            logger.warning(f"Timeout checking {file_id}")
            return False
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

        max_distance = 50
        forward_limit = reference_id + max_distance
        backward_limit = max(reference_id - max_distance, 0)

        # Scan in batches of 10 IDs
        batch_size = 10
        found_reports = False

        try:
            # Process forward IDs in batches
            for start_id in range(reference_id, forward_limit + 1, batch_size):
                end_id = min(start_id + batch_size, forward_limit + 1)
                tasks = [
                    self.check_report_exists(file_id)
                    for file_id in range(start_id, end_id)
                ]
                results = await asyncio.gather(*tasks)

                # Process found IDs
                new_ids = {
                    start_id + i
                    for i, exists in enumerate(results)
                    if exists
                    and not any(start_id + i in ids for ids in self.known_ids.values())
                }

                if new_ids:
                    found_reports = True
                    self.known_ids[date_key].extend(new_ids)
                    self.save_known_ids()
                    await self.download_reports(new_ids)

            # Process backward IDs in batches
            for start_id in range(
                reference_id - batch_size, backward_limit - 1, -batch_size
            ):
                end_id = max(start_id, backward_limit)
                id_range = list(range(end_id, min(start_id + batch_size, reference_id)))
                if not id_range:
                    continue

                tasks = [self.check_report_exists(file_id) for file_id in id_range]
                results = await asyncio.gather(*tasks)

                # Process found IDs
                new_ids = {
                    id_range[i]
                    for i, exists in enumerate(results)
                    if exists
                    and not any(id_range[i] in ids for ids in self.known_ids.values())
                }

                if new_ids:
                    found_reports = True
                    self.known_ids[date_key].extend(new_ids)
                    self.save_known_ids()
                    await self.download_reports(new_ids)

        except Exception as e:
            logger.error(f"Error during scanning: {str(e)}")
            return

        if not found_reports:
            logger.info("No new reports found in today's scan")

        logger.info(f"Completed daily scan for {date_key}")
        # Log statistics
        logger.info(f"Started from reference ID: {reference_id}")
        logger.info(f"Scanned forward up to ID {forward_limit}")
        logger.info(f"Scanned backward down to ID {backward_limit}")
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

        # Download reports in parallel
        async with aiohttp.ClientSession() as session:
            download_tasks = []
            for file_id in report_ids:
                url = self.base_url.format(file_id=file_id)
                download_tasks.append(
                    self._download_single_report(session, file_id, url, download_dir)
                )
            await asyncio.gather(*download_tasks)

        logger.info(f"Completed downloading {len(report_ids)} reports")

    async def _download_single_report(
        self, session: aiohttp.ClientSession, file_id: int, url: str, download_dir: str
    ):
        """Download a single report from the given URL."""
        try:
            async with session.get(url) as response:
                if response.status == 200:
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


async def wait_until_next_run(run_time: time):
    """Suspend execution until the next scheduled run time."""
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
