from typing import Any, Dict, List
from pydantic import BaseModel, validator

from fastapi.responses import JSONResponse

from skit_pipelines.api.models.custom_models import ParseRunResponse
import skit_pipelines.constants as const


class StatusResponseModel(BaseModel):
    message: str
    run_id: str
    run_url: str
    uris: List[str] | None = None
    webhook: bool = False


def customResponse(message: Dict[Any, Any], status_code: int = 200, status: str = "ok") -> JSONResponse:
    return JSONResponse(dict(
        status=status,
        response=message,
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
        _message.uris = run_response.uris
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