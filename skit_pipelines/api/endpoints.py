import asyncio
from datetime import timedelta
from typing import Any, Dict

import kfp
import kfp_server_api
import pydantic
from aiokafka import AIOKafkaProducer
from fastapi import Request
from kfp_server_api.models.api_run_detail import ApiRunDetail as kfp_ApiRunDetail
from loguru import logger

import skit_pipelines.constants as const
from skit_pipelines.api import (
    BackgroundTasks,
    app,
    models,
    run_in_threadpool,
    slack_app,
    slack_handler,
)
from skit_pipelines.api.slack_bot import get_message_data, make_response
from skit_pipelines.utils import filter_schema, kubeflow_login, normalize, webhook_utils

loop = asyncio.get_event_loop()


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


def call_kfp_method(method_fn: str = const.KFP_RUN_FN, *args, **kwargs):
    kf_client = kubeflow_login()
    if not kf_client.get_kfp_healthz().multi_user:
        kf_client = kubeflow_login(force=True)

    client_run = getattr(kf_client, method_fn)(*args, **kwargs)
    return client_run


def get_default_experiment_id(kf_client: kfp.Client):
    experiments = kf_client.list_experiments(namespace=const.KF_NAMESPACE).experiments
    for experiment in experiments:
        if experiment.name == const.DEFAULT_EXPERIMENT_NAME:
            return experiment.id
    raise ValueError(
        f"No experiment named {const.DEFAULT_EXPERIMENT_NAME} found in namespace {const.KF_NAMESPACE}."
    )


def run_kfp(
    kf_client: kfp.Client, pipeline_id: str, pipeline_name: str, params: Dict[str, Any]
):
    experiment_id = get_default_experiment_id(kf_client)
    run_info = kf_client.run_pipeline(
        experiment_id,
        pipeline_name,
        pipeline_id=pipeline_id,
        params=params,
        enable_caching=False,
    )
    return RunPipelineResult(kf_client, run_info)


async def schedule_run_completion(
    client_resp: RunPipelineResult, namespace: str, webhook_url: str
):
    run_resp: kfp_ApiRunDetail = await run_in_threadpool(
        client_resp.wait_for_run_completion
    )
    logger.info(f"Pipeline run finished!")
    parsed_resp = models.ParseRunResponse(run=run_resp, namespace=namespace)
    msg = models.statusWiseResponse(parsed_resp, webhook=bool(webhook_url))
    if webhook_url:
        webhook_utils.send_webhook_request(url=webhook_url, data=msg.body)


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


@app.get("/{namespace}/pipelines/{pipeline_name}/runs/")
def get_run_info(namespace: str, pipeline_name: str, run_id: str):
    run_resp = call_kfp_method(method_fn="get_run", run_id=run_id)

    parsed_resp = models.ParseRunResponse(
        run=run_resp, component_display_name=pipeline_name
    )
    return models.statusWiseResponse(parsed_resp)


@app.post("/{namespace}/pipelines/run/{pipeline_name}/")
def pipeline_run_req(
    *,
    namespace: str,
    pipeline_name: str,
    payload: Dict[str, Any],
    background_tasks: BackgroundTasks,
):
    kf_client = kubeflow_login()
    if not kf_client.get_kfp_healthz().multi_user:
        kf_client = kubeflow_login(force=True)
    pipeline_name = normalize.to_snake_case(pipeline_name)

    pipelines = {
        normalize.to_snake_case(pipeline.name): pipeline.id
        for pipeline in kf_client.list_pipelines().pipelines
    }

    pipeline_names = "\n".join(pipelines.keys())
    if pipeline_name not in pipelines and pipeline_name not in models.RequestSchemas:
        raise models.errors.kfp_api_error(
            reason=f"""Pipeline should be one of: {pipeline_names}.
If your pipeline is present, it is not supported in the official release.""",
            status=400,
        )

    Schema = models.RequestSchemas[pipeline_name]

    try:
        payload = Schema.parse_obj(payload)
    except pydantic.error_wrappers.ValidationError as e:
        raise models.errors.kfp_api_error(reason=str(e), status=400) from e

    run = run_kfp(
        kf_client,
        pipeline_id=pipelines[pipeline_name],
        pipeline_name=pipeline_name,
        params=filter_schema(payload.dict(), const.FILTER_LIST),
    )
    background_tasks.add_task(
        schedule_run_completion,
        client_resp=run,
        namespace=namespace,
        webhook_url=payload.webhook_uri,
    )
    return models.successfulCreationResponse(
        run_id=run.run_id, name=pipeline_name, namespace=namespace
    )


@app.exception_handler(kfp_server_api.ApiException)
async def kfp_api_exception_handler(request, exc):
    return models.customResponse(
        {"message": f"{exc}"},
        status_code=exc.status,
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
    channel_id, message_ts, text = get_message_data(body)
    response = make_response(text)
    say(
        thread_ts=message_ts,
        channel=channel_id,
        unfurl_link=True,
        text=response,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0")
