import kfp
from loguru import logger

from skit_pipelines.utils import cookie_utils
import skit_pipelines.constants as const


def kubeflow_login(force: bool = False) -> kfp.Client:
    if force:
        cookie_dict = cookie_utils.fetch_latest_cookies()
    else:
        try:
            cookie_dict = cookie_utils.load_cookies(const.COOKIES_PATH)
        except FileNotFoundError:
            logger.info(f"{const.COOKIES_PATH} not found, simulating cookie fetch though re-login")
            cookie_dict = cookie_utils.fetch_latest_cookies()

    client = kfp.Client(
            host=const.PIPELINE_HOST_URL,
            cookies=const.CONSTRUCT_COOKIE_TOKEN(cookie_dict)
        )
    return client