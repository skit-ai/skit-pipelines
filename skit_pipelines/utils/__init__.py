from typing import Dict, Any
import os
from datetime import datetime

import skit_pipelines.utils.cookies as cookie_utils
from skit_pipelines.utils.login import kubeflow_login
import skit_pipelines.utils.webhook as webhook_utils
from skit_pipelines.utils.storage import create_storage_path

def create_file_name(org_id: str, file_type: str, ext=".csv") -> str:
    return os.path.join(
        "project",
        str(org_id),
        datetime.now().strftime("%Y-%m-%d"),
        f"{org_id}-{datetime.now().strftime('%Y-%m-%d')}-{file_type}{ext}",
    )


def create_dir_name(org_id: str, dir_type: str) -> str:
    return os.path.join(
        "project", str(org_id), datetime.now().strftime("%Y-%m-%d"), dir_type
    )


class SlackBlockFactory:
    def __init__(self, content) -> None:
        self.body = {"text": "", "blocks": []}
        self.content = content

    def code_block(self, content):
        if not content:
            return self
        format_content = f"""
```
{content}
```
""".strip()
        self.body["blocks"].append(
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": format_content},
            }
        )
        return self

    def text_block(self):
        if not self.content:
            return self
        self.body["blocks"].append(
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": self.content},
            }
        )
        return self

    def ping(self, cc):
        if not cc:
            return self

        names = []
        for name in cc.split(","):
            name = name.strip()
            if name[0] != '@':
                name = f"<@{name}>"
            if not name:
                continue
            names.append(name)
        cc_group = " ".join(names)
        self.content = f"{self.content}\ncc: {cc_group}"
        return self

    def text(self):
        self.body["text"] = self.content
        return self

    def build(self) -> Dict:
        return self.body


def filter_schema(schema: Dict[str, Any], filter_list: list) -> Dict[str, Any]:
    return {
        k: v
        for k, v in schema.items()
        if k not in filter_list
    }