from typing import Optional

import kfp

from skit_pipelines import constants as pipeline_constants


def org_auth_token(org_id: str, url: Optional[str] = None) -> str:
    from skit_auth import auth, utils
    from loguru import logger
    from skit_pipelines import constants as const

    utils.configure_logger(7)

    url = const.CONSOLE_API_URL if not url else url
    try:
        token = auth.get_org_token(
            url, const.CONSOLE_IAM_EMAIL, const.CONSOLE_IAM_PASSWORD, int(org_id)
        )
    except ValueError as exc:
        logger.error(f"Failed to get org token.\n{exc=}")
        token = ""
    return token


org_auth_token_op = kfp.components.create_component_from_func(
    org_auth_token, base_image=pipeline_constants.BASE_IMAGE
)
