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

            job_ids = user["jobs"]
            updated_jobs = []
            for job_id in job_ids:
                try:
                    job = {"id": job_id}
                    job["stars"] = user[f"stars_{int(job_id)}"]
                    job["score"] = user[f"score_{int(job_id)}"]
                    del user[f"stars_{int(job_id)}"]
                    del user[f"score_{int(job_id)}"]
                    updated_jobs.append(job)
                except KeyError:
                    pass

            user["jobs"] = updated_jobs
            copy = user.copy()
            for key in user:
                if str(key).startswith("score_") or str(key).startswith("stars_"):
                    del copy[key]

            user = copy.copy()
