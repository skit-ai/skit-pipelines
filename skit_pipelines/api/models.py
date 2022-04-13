import json
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from kfp_server_api.models.api_run_detail import ApiRunDetail as kfp_ApiRunDetail
import skit_pipelines.constants as const


class FetchCallSchema(BaseModel):
    """
    Fetch Calls schema
    """
    client_id: int
    start_date: str
    lang: str
    end_date: Optional[str] = None
    call_quantity: int = 200
    call_type: str = "inbound"
    ignore_callers: Optional[str] = None
    reported: Optional[str] = None
    use_case: Optional[str] = None
    flow_name: Optional[str] = None
    min_duration: Optional[str] = None
    asr_provider: Optional[str] = None
    notify: Optional[bool] = False
    
    
class ParseRunResponse:
    """
    Run Response parser
    """
    def __init__(self, run: kfp_ApiRunDetail, component_display_name: str):
        self.run = run
        self.id = run.run.id
        self.display_name = component_display_name
        self.parse_response()
        self.url = f"{const.PIPELINE_HOST_URL}/?ns={self.namespace}#/runs/details/{self.id}"
        
    def parse_response(self) -> None:
        workflow_nodes: List[Dict[str, Any]] = json.loads(self.run.pipeline_runtime.workflow_manifest)
        meta: Dict[str, Any] = workflow_nodes["metadata"]
        name: str = meta["name"]
        self.namespace: str = meta['namespace']
        success: bool = workflow_nodes["status"]["phase"] == "Succeeded"
        status_nodes: Dict[str, Dict[str, Any]] = workflow_nodes["status"]["nodes"]
        
        target_node: Dict[str, Any] = [node for node in status_nodes.values() if node["displayName"] == self.display_name][0]
        artifacts: List[Dict[str, Any]] = target_node["outputs"]["artifacts"]
        self.data: Dict[str, Any] = artifacts[0]
        logs: Dict[str, Any] = artifacts[1]
        
        self.data_path: str = self.data['path']
        s3_bucket: str = self.data['s3']['bucket']
        s3_key: str = self.data['s3']['key']
        self.s3_uri: str = f"s3://{s3_bucket}/{s3_key}"