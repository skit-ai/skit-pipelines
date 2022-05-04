from kfp_server_api import ApiException

def kfp_api_error(reason: str, status=503) -> ApiException:
    return ApiException(
        status=status,
        reason=reason
    )