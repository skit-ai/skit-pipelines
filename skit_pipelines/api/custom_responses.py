from typing import Dict, Any
from fastapi.responses import JSONResponse


def basic_response(message: str, status_code: int = 200, status: str = "ok") -> JSONResponse:
    return JSONResponse(dict(
        status=status,
        response={"message": message},
    ), status_code=status_code)

def custom_response(message_dict: Dict[Any, Any], status_code: int = 200, status: str = "ok") -> JSONResponse:
    return JSONResponse(dict(
        status=status,
        response=message_dict,
    ), status_code=status_code)