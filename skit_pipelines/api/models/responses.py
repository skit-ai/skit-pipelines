from typing import Any, Dict, List
from pydantic import BaseModel, validator

from fastapi.responses import JSONResponse

from skit_pipelines.api.models.custom_models import ParseRunResponse
import skit_pipelines.constants as const


class StatusResponseModel(BaseModel):
    message: str
    run_id: str
    run_url: str
    file_path: str | None = None
    s3_path: str | None = None
    webhook: bool = False

def customResponse(message: str | Dict[Any, Any], status_code: int = 200, status: str = "ok") -> JSONResponse:
    return JSONResponse(dict(
        status=status,
        response={"message": message} if isinstance(message, str) else message,
    ), status_code=status_code)
    
def statusWiseResponse(run_response: ParseRunResponse, webhook=False):
    _message = StatusResponseModel(
        message="",
        run_id=run_response.id,
        run_url=run_response.url,
        webhook=webhook
    )
    status = 'ok'
    status_code = 200
    
    if run_response.success:
        _message.message = "Run completed successfully."
        _message.file_path = run_response.data_path
        _message.s3_path = run_response.s3_uri
        
    elif run_response.pending:
        _message.message = "Run in progress."
        status = 'pending'
    
    else:
        _message.message = "Run failed."
        status = 'error'
        status_code = 500
    
    return customResponse(
        message=_message.dict(),
        status=status,
        status_code=status_code
    )

def successfulCreationResponse(run_id: str, name: str, namespace: str):
    return customResponse({
        "message": "Pipeline run created successfully.",
        "name": name,
        "run_id": run_id,
        "run_url": const.GET_RUN_URL(namespace, run_id)
    })