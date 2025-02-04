"""Time tool module.

This module provides functions for getting current time and date information
in various formats. It's designed to be used with LLM APIs to provide
accurate temporal context.
"""

from datetime import datetime
from typing import Any, Dict

import pytz

from tools.core.tool_protocol import Tool


def get_current_time(timezone="Asia/Taipei"):
    """Get current time in specified timezone.

    Args:
        timezone (str): Timezone name (e.g., 'UTC', 'Asia/Taipei'). Defaults to 'Asia/Taipei'.

    Returns:
        dict: Dictionary containing current time information in various formats
    """
    try:
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)

        return {
            "iso_format": now.isoformat(),
            "date": now.date().isoformat(),
            "time": now.time().isoformat(),
            "timestamp": int(now.timestamp()),
            "timezone": timezone,
            "readable_format": now.strftime("%Y-%m-%d %H:%M:%S %Z"),
            "year": now.year,
            "month": now.month,
            "day": now.day,
            "hour": now.hour,
            "minute": now.minute,
            "second": now.second,
            "weekday": now.strftime("%A"),
        }
    except pytz.exceptions.UnknownTimeZoneError:
        return {"error": f"Unknown timezone: {timezone}"}


class TimeTool(Tool):
    """Tool for getting current time."""

    async def execute(self, input_data: Dict[str, Any]) -> Any:
        """Get current time for specified timezone.

        Args:
            input_data: Dictionary optionally containing 'timezone' key (defaults to 'Asia/Taipei')

        Returns:
            Current time in specified timezone
        """
        return get_current_time(input_data.get("timezone", "Asia/Taipei"))


def main():
    """Command-line interface for the time tool."""
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Get current time information")
    parser.add_argument(
        "--timezone",
        type=str,
        default="Asia/Taipei",
        help="Timezone (e.g., UTC, Asia/Taipei)",
    )
    parser.add_argument(
        "--format",
        choices=["json", "readable"],
        default="readable",
        help="Output format",
    )

    args = parser.parse_args()
    time_info = get_current_time(args.timezone)

    if args.format == "json":
        print(json.dumps(time_info, indent=2))
    else:
        print(time_info["readable_format"])


if __name__ == "__main__":
    main()
