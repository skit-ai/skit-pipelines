from typing import Dict
import kfp
import kfp_server_api
from loguru import logger
import asyncio
from aiokafka import AIOKafkaProducer

from kfp_server_api.models.api_run_detail import ApiRunDetail as kfp_ApiRunDetail

from skit_pipelines.api import app, models, BackgroundTasks, run_in_threadpool
from skit_pipelines.utils.config import config
from skit_pipelines.utils import kubeflow_login, webhook_utils, filter_schema
import skit_pipelines.constants as const


KF_CLIENT: kfp.Client

loop = asyncio.get_event_loop()
aioproducer = AIOKafkaProducer(
    loop=loop, client_id=const.PROJECT_NAME, bootstrap_servers=const.KAFKA_INSTANCE
)

class RunPipelineResult:
    def __init__(self, client, run_info):
        self._client: kfp.Client = client
        self.run_info = run_info
        self.run_id = run_info.id

    def wait_for_run_completion(self, timeout=None):
        timeout = timeout or timedelta.max
        return self._client.wait_for_run_completion(self.run_id, timeout)

    def __repr__(self):
        return 'RunPipelineResult(run_id={})'.format(self.run_id)


def call_kfp_method(method_fn: str = const.KFP_RUN_FN, *args, **kwargs):
    kf_client = kubeflow_login()
    if not kf_client.get_kfp_healthz().multi_user:
        kf_client = kubeflow_login(force=True)

    client_run = getattr(kf_client, method_fn)(*args, **kwargs)
    return client_run


async def schedule_run_completion(
    client_resp,
    namespace: str,
    component_name: str,
    payload: models.BaseRequestSchema,
    webhook_url: str
):
    webhook_req = True if webhook_url else False
    run_resp: kfp_ApiRunDetail  = await run_in_threadpool(client_resp.wait_for_run_completion)
    logger.info(f"Pipeline run for {component_name} finished!")
    parsed_resp = models.ParseRunResponse(run=run_resp, component_display_name=component_name)
    msg = models.statusWiseResponse(parsed_resp, webhook=webhook_req)
    await aioproducer.send(config.KAFKA_TOPIC_MAP[component_name], msg.body)
    logger.info((f"Results sent to queue."))
    if webhook_req:
        webhook_utils.send_webhook_request(url=webhook_url, data=msg.body)
        


@app.on_event("startup")
async def startup_event():
    logger.info("Starting Up...")
    logger.info("Initializing kubeflow client.")
    global KF_CLIENT
    KF_CLIENT = kubeflow_login()
    await aioproducer.start()
    logger.info("Kubeflow client initialized.")


@app.on_event("shutdown")
async def shutdown_event():
    await aioproducer.stop()
    logger.info("Stopping server...")
    

@app.get("/")
def health_check():
    """
    Get server status health.
    The purpose of this API is to help other people/machines know liveness of the application.
    """
    logger.info("Health check pinged!")
    KF_CLIENT = kubeflow_login()
    if KF_CLIENT.get_kfp_healthz().multi_user:
        return models.customResponse("Kubeflow server communication is up!")
    else:
        raise models.errors.kfp_api_error(
            reason="Unable to communicate with Kubeflow server..."
        )


@app.get("/{namespace}/pipelines/{pipeline_name}/runs/")
def get_run_info(
    namespace: str,
    pipeline_name: str,
    run_id: str
):
    run_resp = call_kfp_method(
        method_fn="get_run",
        run_id=run_id
    )

    parsed_resp = models.ParseRunResponse(run=run_resp, component_display_name=pipeline_name)
    return models.statusWiseResponse(parsed_resp)

@app.post("/{namespace}/pipelines/run/{pipeline_name}/")
def pipeline_run_req(*,
    namespace: str,
    pipeline_name: str,
    run_name: str | None = None,
    component_name: str | None = None,
    payload: models.ValidRequestSchemas,
    background_tasks: BackgroundTasks
):
    if not config.valid_pipeline(pipeline_name):
        raise models.errors.kfp_api_error(
            reason=f"Invalid pipeline requested, check if it exists: {pipeline_name}",
            status=400
        )
    
    run_name = run_name if run_name else config.RUN_NAME_MAP[pipeline_name]
    component_name = component_name if component_name else pipeline_name
    run = call_kfp_method(
        pipeline_func=config.PIPELINE_FN_MAP[pipeline_name],
        run_name=run_name,
        namespace=namespace,
        arguments=filter_schema(payload.dict(), const.FILTER_LIST)
    )
    background_tasks.add_task(
        schedule_run_completion,
        client_resp=run,
        namespace=namespace,
        component_name=component_name,
        payload=payload,
        webhook_url=payload.webhook_uri
    )
    return models.successfulCreationResponse(
        run_id=run.run_id,
        name=pipeline_name,
        namespace=namespace
    )



@app.exception_handler(kfp_server_api.ApiException)
async def kfp_api_exception_handler(request, exc):
    return models.customResponse(
        status_code=exc.status,
        message=f"{exc}",
        status="error",
    )



if __name__ == "__main__":
    app.run(host="0.0.0.0")
