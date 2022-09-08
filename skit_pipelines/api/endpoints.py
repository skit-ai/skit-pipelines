import json
from datetime import timedelta
from typing import Any, Callable, Dict, Optional

import kfp
import kfp_server_api
import pydantic
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from kfp_server_api.models.api_run_detail import ApiRunDetail as kfp_ApiRunDetail
from loguru import logger

import skit_pipelines.constants as const
from skit_pipelines.api import (
    BackgroundTasks,
    app,
    auth,
    models,
    run_in_threadpool,
    slack_app,
    slack_handler,
)
from skit_pipelines.api.slack_bot import get_message_data, make_response
from skit_pipelines.components.notification import slack_notification
from skit_pipelines.utils import filter_schema, kubeflow_login, normalize, webhook_utils


class RunPipelineResult:
    def __init__(self, client, run_info):
        self._client: kfp.Client = client
        self.run_info = run_info
        self.run_id = run_info.id

    def wait_for_run_completion(self, timeout=None):
        timeout = timeout or timedelta.max
        return self._client.wait_for_run_completion(self.run_id, timeout)

    def __repr__(self):
        return "RunPipelineResult(run_id={})".format(self.run_id)


@app.post("/token", response_model=models.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = auth.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


def run_kfp_pipeline_func(
    kf_client: kfp.Client,
    pipeline_func: Callable,
    params: Dict[str, Any],
    experiment_name: str = const.DEFAULT_EXPERIMENT_NAME,
    namespace: str = const.KF_NAMESPACE,
) -> RunPipelineResult:
    return kf_client.create_run_from_pipeline_func(
        pipeline_func=pipeline_func,
        arguments=params,
        experiment_name=experiment_name,
        namespace=namespace,
        enable_caching=False,
    )


async def schedule_run_completion(
    client_resp: RunPipelineResult,
    namespace: str,
    webhook_url: str,
    slack_channel: Optional[str] = None,
    slack_thread: Optional[float] = None,
):
    run_resp: kfp_ApiRunDetail = await run_in_threadpool(
        client_resp.wait_for_run_completion
    )
    logger.info(f"Pipeline run finished!")
    parsed_resp = models.ParseRunResponse(run=run_resp, namespace=namespace)
    msg = models.statusWiseResponse(parsed_resp, webhook=bool(webhook_url))
    if webhook_url:
        webhook_utils.send_webhook_request(url=webhook_url, data=msg.body)

    if slack_thread and slack_channel:
        res = json.loads(msg.body.decode("utf8"))
        message = res.get("response", {}).get("message")
        url = res.get("response", {}).get("run_url")
        message = f"<{url}|{message}>"
        slack_notification(message, channel=slack_channel, thread_id=slack_thread)


@app.get("/")
def health_check():
    """
    Get server status health.
    The purpose of this API is to help other people/machines know liveness of the application.
    """
    logger.info("Health check pinged!")
    kf_client = kubeflow_login()
    if kf_client.get_kfp_healthz().multi_user:
        return models.customResponse(
            {"message": "Kubeflow server communication is up!"}
        )
    else:
        raise models.errors.kfp_api_error(
            reason="Unable to communicate with Kubeflow server..."
        )


@app.post("/{namespace}/pipelines/run/{pipeline_name}/")
def pipeline_run_req(
    *,
    namespace: str,
    pipeline_name: str,
    payload: Dict[str, Any],
    background_tasks: BackgroundTasks,
    _: str = Depends(auth.valid_user),
):
    kf_client = kubeflow_login()
    if not kf_client.get_kfp_healthz().multi_user:
        kf_client = kubeflow_login(force=True)

    req_pipeline_name = normalize.to_snake_case(pipeline_name)
    pipelines = models.get_normalized_pipelines_fn_map()

    if not (Schema := models.RequestSchemas.get(req_pipeline_name)):
        raise models.errors.kfp_api_error(
            reason="""Pipeline should be one of: {}.
If your pipeline is present, it is not supported in the official release.""".format(
                "\n".join(pipelines.keys())
            ),
            status=400,
        )

    payload = Schema.parse_obj(payload)

    run = run_kfp_pipeline_func(
        kf_client,
        pipeline_func=pipelines[req_pipeline_name],
        params=filter_schema(payload.dict(), const.FILTER_LIST),
    )

    background_tasks.add_task(
        schedule_run_completion,
        client_resp=run,
        namespace=namespace,
        webhook_url=payload.webhook_uri,
        slack_channel=payload.channel,
        slack_thread=payload.slack_thread,
    )

    return models.successfulCreationResponse(
        run_id=run.run_id, name=req_pipeline_name, namespace=namespace
    )


@app.exception_handler(kfp_server_api.ApiException)
async def kfp_api_exception_handler(request, exc):
    return models.customResponse(
        {"message": f"{exc}"},
        status_code=exc.status,
        status="error",
    )


@app.exception_handler(pydantic.error_wrappers.ValidationError)
async def arguments_validation_exception_handler(request, exc):
    # TODO: give better error messages as where validation problem
    return models.customResponse(
        {"message": f"{exc}"},
        status_code=400,
        status="error",
    )


@app.post("/slack/events")
async def endpoint(req: Request):
    return await slack_handler.handle(req)


@slack_app.event("app_mention")
def handle_app_mention_events(body, say, logger):
    """
    This function is called when the bot (@charon) is called in any slack channel.

    :param body: [description]
    :type body: [type]
    :param say: [description]
    :type say: [type]
    :param _: [description]
    :type _: [type]
    """
    channel_id, message_ts, text, user = get_message_data(body)
    response = make_response(channel_id, message_ts, text, user)
    say(
        thread_ts=message_ts,
        channel=channel_id,
        unfurl_link=True,
        text=response,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0")
