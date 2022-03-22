import os
from datetime import datetime


def create_file_name(org_id: int, file_type: str, ext=".csv") -> str:
    return os.path.join(
        "project",
        str(org_id),
        datetime.now().strftime("%Y-%m-%d"),
        f"{org_id}-{datetime.now().strftime('%Y-%m-%d')}-{file_type}{ext}",
    )


def help_aws_s3_cp(s3_path: str) -> None:
    return f"""
```
aws s3 cp {s3_path} .
```
"""

