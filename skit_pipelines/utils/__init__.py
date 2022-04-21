from typing import Dict
import os
from datetime import datetime

import skit_pipelines.utils.cookies as cookie_utils
from skit_pipelines.utils.login import kubeflow_login

def create_file_name(org_id: int, file_type: str, ext=".csv") -> str:
    return os.path.join(
        "project",
        str(org_id),
        datetime.now().strftime("%Y-%m-%d"),
        f"{org_id}-{datetime.now().strftime('%Y-%m-%d')}-{file_type}{ext}",
    )


def create_dir_name(org_id: int, dir_type: str) -> str:
    return os.path.join(
        "project", str(org_id), datetime.now().strftime("%Y-%m-%d"), dir_type
    )


class SlackBlockFactory:
    def __init__(self) -> None:
        self.message = {"text": "", "blocks": []}

    def code_block(self, content):
        if not content:
            return self
        content = f"""
```
{content}
```
""".strip()
        self.message["blocks"].append(
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": content},
            }
        )
        return self

    def text_block(self, content):
        if not content:
            return self
        self.message["blocks"].append(
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": content},
            }
        )
        return self

    def text(self, content):
        self.message["text"] = content
        return self

    def build(self) -> Dict:
        return self.message
