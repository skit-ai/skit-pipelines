import json
from typing import Any, Dict, List
from pydantic import BaseModel, validator

from kfp_server_api.models.api_run_detail import ApiRunDetail as kfp_ApiRunDetail
import skit_pipelines.constants as const


class BasePayloadSchema(BaseModel):
    @validator('*', pre=True)
    def transform_none(cls, value):
        if value is None:
            return ""
        return value
        

class FetchCallSchema(BasePayloadSchema):
    """
    Fetch Calls schema
    """
    client_id: int
    start_date: str
    lang: str
    end_date: str | None = ""
    call_quantity: int = 200
    call_type: str = "inbound"
    ignore_callers: str | None = ""
    reported: str | None = ""
    use_case: str | None = ""
    flow_name: str | None = ""
    min_duration: str | None = ""
    asr_provider: str | None = ""
    notify: bool | None = False
    

class TagCallSchema(BasePayloadSchema):
    """
    Tag Calls Schema
    """
    org_id: int
    job_id: int
    s3_path: str
    notify: str | None = False
    
class ParseRunResponse:
    """
    Run Response parser
    """
    def __init__(self, run: kfp_ApiRunDetail, component_display_name: str):
        self.run = run
        self.id = run.run.id
        self.display_name = component_display_name
        self.parse_response()
        self.url = const.GET_RUN_URL(self.namespace, self.id)
        
    def parse_response(self) -> None:
        workflow_nodes: List[Dict[str, Any]] = json.loads(self.run.pipeline_runtime.workflow_manifest)
        meta: Dict[str, Any] = workflow_nodes["metadata"]
        name: str = meta["name"]
        self.namespace: str = meta['namespace']
        current_status: Dict[str, Any] = workflow_nodes["status"]["phase"]
        self.pending: bool = (current_status is None) or (current_status.lower() not in ['succeeded', 'failed', 'skipped', 'error'])
        self.success: bool = current_status == "Succeeded"
        if (not self.success) or self.pending:
            return
        status_nodes: Dict[str, Dict[str, Any]] = workflow_nodes["status"]["nodes"]
        
        target_node: Dict[str, Any] = [node for node in status_nodes.values() if node["displayName"] == self.display_name][0]
        artifacts: List[Dict[str, Any]] = target_node["outputs"]["artifacts"]
        self.data: Dict[str, Any] = artifacts[0]
        logs: Dict[str, Any] = artifacts[1]
        
        self.data_path: str = self.data['path']
        s3_bucket: str = self.data['s3']['bucket']
        s3_key: str = self.data['s3']['key']
        self.s3_uri: str = f"s3://{s3_bucket}/{s3_key}"