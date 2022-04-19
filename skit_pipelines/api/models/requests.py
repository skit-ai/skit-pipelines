from typing import Any, Dict, List
from pydantic import BaseModel, validator

class BaseRequestSchema(BaseModel):
    @validator('*', pre=True)
    def transform_none(cls, value):
        if value is None:
            return ""
        return value


class FetchCallSchema(BaseRequestSchema):
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


class TagCallSchema(BaseRequestSchema):
    """
    Tag Calls Schema
    """
    org_id: int
    job_id: int
    s3_path: str
    notify: str | None = False