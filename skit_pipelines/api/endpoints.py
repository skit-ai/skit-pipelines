import kfp
import kfp_server_api
from loguru import logger
import asyncio
from aiokafka import AIOKafkaProducer

from kfp_server_api.models.api_run_detail import ApiRunDetail as kfp_ApiRunDetail

from skit_pipelines.api import app, models, BackgroundTasks, run_in_threadpool
from skit_pipelines.pipelines import (
    run_fetch_calls,
    run_tag_calls
)
from skit_pipelines.utils import kubeflow_login
import skit_pipelines.constants as const


KF_CLIENT: kfp.Client

loop = asyncio.get_event_loop()
aioproducer = AIOKafkaProducer(
    loop=loop, client_id=const.PROJECT_NAME, bootstrap_servers=const.KAFKA_INSTANCE
)


def call_kfp_method(method_fn: str = const.KFP_RUN_FN, *args, **kwargs):
    global KF_CLIENT
    KF_CLIENT = kubeflow_login()
    if not KF_CLIENT.get_kfp_healthz().multi_user:
        KF_CLIENT = kubeflow_login(force=True)

    client_run = getattr(KF_CLIENT, method_fn)(*args, **kwargs)
    return client_run


async def schedule_run_completion(
    client_resp,
    namespace: str,
    component_name: str,
    payload: models.BaseRequestSchema
):
    run_resp: kfp_ApiRunDetail  = await run_in_threadpool(client_resp.wait_for_run_completion)
    logger.info(f"Pipeline run for {component_name} finished!")
    parsed_resp = models.ParseRunResponse(run=run_resp, component_display_name=component_name)
    msg = models.statusWiseResponse(parsed_resp)
    await aioproducer.send(const.KAFKA_TOPIC_MAP[component_name], msg.body)
    logger.info((f"Results sent to queue."))


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
    KF_CLIENT = kubeflow_login()
    if KF_CLIENT.get_kfp_healthz().multi_user:
        return models.customResponse("Kubeflow server communication is up!")
    else:
        raise kfp_server_api.ApiException(
            status=503,
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


@app.post("/{namespace}/pipelines/run/fetch-calls/")
def fetch_calls_req(*,
    namespace: str,
    payload: models.FetchCallSchema,
    run_name: str = const.DEFAULT_FETCH_CALLS_API_RUN,
    component_name: str = const.FETCH_CALLS_NAME,
    background_tasks: BackgroundTasks
):
    run = call_kfp_method(
        pipeline_func=run_fetch_calls,
        run_name=run_name,
        namespace=namespace,
        arguments=payload.dict()
    )
    background_tasks.add_task(
        schedule_run_completion,
        client_resp=run,
        namespace=namespace,
        component_name=component_name,
        payload=payload
    )
    return models.successfulCreationResponse(
        run_id=run.run_id,
        name=const.FETCH_CALLS_NAME,
        namespace=namespace
    )
    

@app.post("/{namespace}/pipelines/run/tag-calls/")
def tag_calls_req(*,
    namespace: str,
    payload: models.TagCallSchema,
    run_name: str = const.DEFAULT_TAG_CALLS_API_RUN,
    component_name: str = const.FETCH_CALLS_NAME,
    background_tasks: BackgroundTasks
):
    run = call_kfp_method(
        pipeline_func=run_tag_calls,
        run_name=run_name,
        namespace=namespace,
        arguments=payload.dict()
    )
    background_tasks.add_task(
        schedule_run_completion,
        client_resp=run,
        namespace=namespace,
        component_name=component_name,
        payload=payload
    )
    return models.successfulCreationResponse(
        run_id=run.run_id,
        name=const.TAG_CALLS_NAME,
        namespace=namespace
    )


@app.exception_handler(kfp_server_api.ApiException)
async def kfp_api_exception_handler(request, exc):
    return models.customResponse(
        status_code=exc.status,
        message_dict=f"{exc}",
        status="error",
    )



if __name__ == "__main__":
    app.run(host="0.0.0.0")
