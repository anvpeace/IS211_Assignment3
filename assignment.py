import argparse
import csv
import re
import sys
import urllib.request
from collections import Counter
from datetime import datetime

# Personal Notes to help me understand better:
# uses regex to search for files ending in 'jpg', 'gif', 'png' and stores data in a variable
# ignore case mode can be removed but gave issues when image type was capitalized
# .IGNORECASE essentially ignores the case of the letter
IMAGE_RE = re.compile(r"\.(jpg|gif|png)$", re.IGNORECASE)


BROWSER_PATTERNS = [
    ("Internet Explorer", re.compile(r"(MSIE|Trident/)", re.IGNORECASE)),
    ("Chrome", re.compile(r"Chrome/", re.IGNORECASE)),
    ("Firefox", re.compile(r"Firefox/", re.IGNORECASE)),
    ("Safari", re.compile(r"Safari/", re.IGNORECASE)),
]


def parse_args():
    parser = argparse.ArgumentParser(description="Process a web log CSV and output stats.")
    parser.add_argument(
        "--url",
        required=True,
        help="URL to the web log CSV file"
    )
    return parser.parse_args()


def download_text(url):
    """Download the file at `url` and return it as decoded text."""
    try:
        with urllib.request.urlopen(url) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"Error downloading file from URL: {url}\n{e}", file=sys.stderr)
        sys.exit(1)


def detect_browser(user_agent):
    """Return one of: Firefox, Chrome, Internet Explorer, Safari, or Other."""
    for name, pattern in BROWSER_PATTERNS:
        if pattern.search(user_agent):
            return name
    return "Other"


def process_log(csv_text):
    """
    CSV rows:
    1. total hits
    2, image hits
    3. browser counts
    4. hour counts 
    """
    total_hits = 0
    image_hits = 0
    browser_counts = Counter()
    hour_counts = Counter({h: 0 for h in range(24)})  

    reader = csv.reader(csv_text.splitlines())

    for row_num, row in enumerate(reader, start=1):
    # Personal notes to keep track of columns:
    #  0 = path, 1 = datetime, 2 = user-agent, 3 = status, 4 = bytes
        if len(row) < 3:
            continue

        path = row[0].strip()
        dt_str = row[1].strip() if len(row) > 1 else ""
        user_agent = row[2].strip()
        total_hits += 1

        if IMAGE_RE.search(path):
            image_hits += 1


        browser = detect_browser(user_agent)
        browser_counts[browser] += 1

        try:
            dt = datetime.strptime(dt_str, "%m/%d/%Y %H:%M:%S")
            hour_counts[dt.hour] += 1
        except ValueError:
            pass

    return total_hits, image_hits, browser_counts, hour_counts


def main():
    args = parse_args()
    csv_text = download_text(args.url)

    total_hits, image_hits, browser_counts, hour_counts = process_log(csv_text)

    if total_hits == 0:
        print("No hits found in the log file.")
        sys.exit(0)

    pct_images = (image_hits / total_hits) * 100
    print(f"Image requests account for {pct_images:.1f}% of all requests")


    most_common = browser_counts.most_common(1)
    if most_common:
        browser_name, count = most_common[0]
        print(f"Most popular browser: {browser_name} ({count} hits)")

    print("\nHourly hit totals:")
    for hour, hits in sorted(hour_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"Hour {hour:02d} has {hits} hits")


if __name__ == "__main__":
    main()