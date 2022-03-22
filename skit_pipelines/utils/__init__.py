import os
from datetime import datetime


def create_file_name(org_id: int, file_type: str, ext=".csv") -> str:
    return os.path.join(
        "project",
        str(org_id),
        datetime.now().strftime("%Y-%m-%d"),
        f"{org_id}-{datetime.now().strftime('%Y-%m-%d')}-{file_type}{ext}",
    )
