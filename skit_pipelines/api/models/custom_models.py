import json
import os
import tempfile
from typing import Any, Dict, Iterable, List

from kfp_server_api.models.api_run_detail import ApiRunDetail as kfp_ApiRunDetail
from loguru import logger

import skit_pipelines.constants as const
from skit_pipelines.components.download_from_s3 import download_file_from_s3


def filter_artifact_nodes(nodes: Dict[str, Any], **filter_map) -> List[Dict[str, Any]]:
    req_nodes = []
    for node in nodes.values():
        skip = False
        for filter_key, filter_value in filter_map.items():
            if node[filter_key] != filter_value:
                skip = True
        if not skip:
            req_nodes.append(node)
    return req_nodes


def get_kf_object_uri(obj: Dict[str, Any], store="s3") -> str:
    key = obj[store][const.ARTIFACT_URI_KEY]
    bucket = obj[store].get(const.OBJECT_BUCKET, const.KUBEFLOW_SANDBOX_BUCKET)
    if store == "s3":
        return f"s3://{bucket}/{key}"
    else:
        raise ValueError(f"Unsupported store: {store}")


def artifact_node_to_uri(node: Dict[str, Any], store="s3") -> Iterable[str]:
    artifacts: List[Dict[str, Any]] = node[const.NODE_OUTPUT][const.NODE_ARTIFACTS]
    objects: List[Dict[str, Any]] = filter(
        lambda artifact: store in artifact, artifacts
    )
    return map(lambda obj: get_kf_object_uri(obj, store=store), objects)


class ParseRunResponse:
    """
    Run Response parser
    """

    def __init__(self, namespace: str, run: kfp_ApiRunDetail):
        self.run = run
        self.id = run.run.id
        self.url = const.GET_RUN_URL(namespace, self.id)
        self.artifact_nodes: Dict[str, Dict[str, Any]] = {}
        self.pending = False
        self.success = False
        self.error_logs = ""
        self.uris = self.parse_response()

    def set_state(self, current_status) -> bool:
        self.pending = (current_status is None) or (
            current_status.lower() not in {"succeeded", "failed", "skipped", "error"}
        )
        self.success = current_status == "Succeeded"

    def parse_response(self) -> None:
        run_manifest: List[Dict[str, Any]] = json.loads(
            self.run.pipeline_runtime.workflow_manifest
        )
        current_status = run_manifest["status"]["phase"]
        self.set_state(current_status)

        if not self.success:
            self.failed_artifact_nodes = filter_artifact_nodes(
                run_manifest["status"]["nodes"],
                type=const.NODE_TYPE_POD,
                phase="Failed",
            )
            failed_logs_uri = [
                uri
                for obj in map(artifact_node_to_uri, self.failed_artifact_nodes)
                for uri in obj
            ]
            self.set_error_logs(failed_logs_uri)
            return

        self.artifact_nodes = filter_artifact_nodes(
            run_manifest["status"]["nodes"], type=const.NODE_TYPE_POD
        )
        return [
            uri for obj in map(artifact_node_to_uri, self.artifact_nodes) for uri in obj
        ]

    def set_error_logs(self, uris):
        for log_uri in uris:
            _, file_path = tempfile.mkstemp(suffix=".txt")
        download_file_from_s3(storage_path=log_uri, output_path=file_path)
        with open(file_path, "r") as log_file:
            log_text = log_file.read()
            logger.error(log_text)
            self.error_logs += log_text
        os.remove(file_path)  # delete temp log file
