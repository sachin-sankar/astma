import sys
import time
from json import dumps
from pathlib import Path

import requests
from loguru import logger

# Configuration
DATASET_DIR = Path("artifacts/raw_json")
DATASET_DIR.mkdir(exist_ok=True, parents=True)
STEP = 10  # Offset increment value


def get_for_offset(session: requests.Session, offset: int) -> list:
    """Fetches user data for a specific offset."""
    url = f"https://www.freelancer.in/ajax/directory/getFreelancer.php?offset={offset}"

    # Use standard timeout to prevent the script from hanging indefinitely
    resp = session.get(url, timeout=10)
    resp.raise_for_status()

    data = resp.json()
    return data.get("users", [])


def get_last_offset() -> int:
    """Scans the directory for existing individual offset files to resume collection."""
    existing_files = list(DATASET_DIR.glob("*.json"))
    if not existing_files:
        return -STEP

    highest_offset = -STEP
    for file in existing_files:
        try:
            # Parse the offset out of the filename (e.g., '10.json' -> 10)
            offset_val = int(file.stem)
            highest_offset = max(highest_offset, offset_val)
        except ValueError:
            continue

    return highest_offset


def driver():
    # Using a session object reuses the underlying TCP connection for speed
    with requests.Session() as session:
        session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )

        # 1. Check folder history to resume checkpoint
        last_processed = get_last_offset()
        current_offset = last_processed + STEP
        logger.info(f"Resuming collection pipeline from offset: {current_offset}")

        while True:
            try:
                logger.info(f"Fetching offset: {current_offset}")
                users = get_for_offset(session, current_offset)

                if not users:
                    logger.warning(
                        f"No users returned at offset {current_offset}. Stopping."
                    )
                    break

                # 2. Save individual offset file directly to disk
                output_file = DATASET_DIR / f"{current_offset}.json"

                # Open natively without async overhead
                with open(output_file, "w", encoding="utf-8") as file:
                    file.write(dumps(users, indent=4))

                logger.success(f"Saved {len(users)} records into {current_offset}.json")

                # 3. Move window forward linearly
                current_offset += STEP

                # Optional: Polite delay to avoid rate limits/IP bans
                time.sleep(1)

            except requests.RequestException as err:
                logger.error(f"Network error at offset {current_offset}: {err}")
                logger.info("Retrying in 5 seconds...")
                time.sleep(5)


if __name__ == "__main__":
    try:
        driver()
    except KeyboardInterrupt:
        logger.warning("\nScraper safely stopped by user.")
        sys.exit(0)
