from typing import List, Dict, Any
import json
import requests
from loguru import logger


def validate_request_success(resp: requests.Response | str):
    """
    Validate the response from the webhook request
    """
    return not isinstance(resp, str) and resp.status_code in [200, 201]


def send_webhook_request(url: str, data: Dict[str, Any]):
    """
    Send finished runs to the webhook url
    """
    try:
        response = requests.post(url, json=data)
        if validate_request_success(response):
            logger.info(f"Successfully sent webhook request to {url=} and {response.text=}")
        else:
            logger.error(f"Webhook response gave {response.status_code=} and {response.text=}")
    except Exception as e:
        response = f"Unable to send webhook request: {e}"
        logger.error(response)
    return response
