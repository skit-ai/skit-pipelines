import kfp
from kfp.components import OutputPath

from skit_pipelines import constants as pipeline_constants


def org_auth_token(
    org_id: int,
    url: str | None = None
) -> str:
    from skit_auth import auth, utils
    from skit_pipelines import constants as const
    utils.configure_logger(7)
    
    url = const.CONSOLE_API_URL if not url else url
    token = auth.get_org_token(
        url,
        const.CONSOLE_IAM_EMAIL,
        const.CONSOLE_IAM_PASSWORD,
        org_id
    )
    return token

org_auth_token_op = kfp.components.create_component_from_func(
    org_auth_token, base_image=pipeline_constants.BASE_IMAGE
)
