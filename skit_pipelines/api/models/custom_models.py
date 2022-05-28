import json
from typing import Any, Dict, List, Iterable

from kfp_server_api.models.api_run_detail import ApiRunDetail as kfp_ApiRunDetail

import skit_pipelines.constants as const


def filter_artifact_nodes(nodes: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [node for node in nodes.values() if node[const.NODE_TYPE] == const.NODE_TYPE_POD]


def get_kf_object_uri(obj: Dict[str, Any], store = "s3") -> str:
    key = obj[store][const.ARTIFACT_URI_KEY]
    bucket = obj[store][const.OBJECT_BUCKET]
    match store:
        case "s3": return f's3://{bucket}/{key}'
        case _: raise ValueError(f"Unsupported store: {store}")


def artifact_node_to_uri(node: Dict[str, Any], store="s3") -> Iterable[str]:
    artifacts: List[Dict[str, Any]] = node[const.NODE_OUTPUT][const.NODE_ARTIFACTS]
    objects: List[Dict[str, Any]] = filter(lambda artifact: store in artifact, artifacts)
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
        self.uris = self.parse_response()

    def set_state(self, current_status) -> bool:
        self.pending = (current_status is None) or (current_status.lower() not in {'succeeded', 'failed', 'skipped', 'error'})
        self.success = current_status == "Succeeded"

    def parse_response(self) -> None:
        run_manifest: List[Dict[str, Any]] = json.loads(self.run.pipeline_runtime.workflow_manifest)
        current_status = run_manifest["status"]["phase"]
        self.set_state(current_status)

        if not self.success:
            return

        self.artifact_nodes = filter_artifact_nodes(run_manifest["status"]["nodes"])
        return [uri
                for obj in map(artifact_node_to_uri, self.artifact_nodes) 
                for uri in obj]
