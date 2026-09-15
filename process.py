from json import load
from pathlib import Path


def process_file(filepath: Path):
    with open(filepath) as file:
        loaded = load(file)

        # DEL useless keys
        DEL_KEYS = [
            "hidden",
            "penalty",
            "penalty_status",
            "exams",
            "pool_ids",
            "custom_fields",
            "idx",
            "is_online",
            "rating_stars",
            "rating_stars_width",
            "earnings_display",
            "logo_url",
            "profile_logo",
            "flag_icon",
            "flag_name",
            "membership_badge",
            "is_sponsored",
            "is_hilighted",
            "invited",
            "profile_url",
            "rating_stars_count",
            "eh_stars",
            "eh_no_reviews",
        ]
        for user in loaded:
            for KEY in DEL_KEYS:
                del user[KEY]
