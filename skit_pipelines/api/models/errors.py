from kfp_server_api import ApiException

def kfp_invalid_name(message: str) -> ApiException:
    return ApiException(
        status=400,
        reason=message
    )