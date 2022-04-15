import kfp
import kfp_server_api
from loguru import logger

from skit_pipelines.api import app
from skit_pipelines.api.models import (
    FetchCallSchema,
    TagCallSchema,
    ParseRunResponse
)
from skit_pipelines.api.custom_responses import basic_response, custom_response
from skit_pipelines.pipelines import (
    run_fetch_calls,
    run_tag_calls
)
from skit_pipelines.utils import kubeflow_login
import skit_pipelines.constants as const


KF_CLIENT: kfp.Client

@app.exception_handler(kfp_server_api.ApiException)
async def kfp_api_exception_handler(request, exc):
    return custom_response(
        status_code=exc.status,
        message_dict=f"{exc}",
        status="error",
    )


def call_kfp_method(method_fn: str = const.KFP_RUN_FN, *args, **kwargs):
    global KF_CLIENT
    KF_CLIENT = kubeflow_login()
    if not KF_CLIENT.get_kfp_healthz().multi_user:
        KF_CLIENT = kubeflow_login(force=True)

    client_run = getattr(KF_CLIENT, method_fn)(*args, **kwargs)
    return client_run


@app.on_event("startup")
def startup_event():
    logger.info("Starting Up...")
    logger.info("Initializing kubeflow client.")
    global KF_CLIENT
    KF_CLIENT = kubeflow_login()
    logger.info("Kubeflow client initialized.")


@app.get("/")
def health_check():
    """
    Get server status health.
    The purpose of this API is to help other people/machines know liveness of the application.
    """
    return basic_response("Kubeflow pipeline server is up.")


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
    
    parsed_resp = ParseRunResponse(run=run_resp, component_display_name=pipeline_name)
    if parsed_resp.success:
        return custom_response({
            "message": "Run completed successfully.",
            "run_url": parsed_resp.url,
            "file_path": parsed_resp.data_path,
            "s3_path": parsed_resp.s3_uri
        })
    elif parsed_resp.pending:
        return custom_response({
            "message": "Run in progress.",
            "run_url": parsed_resp.url,
            "file_path": None,
            "s3_path": None
        }, status="pending")
    else:
        return custom_response({
            "message": "Run Failed.",
            "run_url": parsed_resp.url,
            "file_path": None,
            "s3_path": None
        }, status_code=500, status="error")


@app.post("/{namespace}/pipelines/run/fetch-calls/")
def fetch_calls_req(
    namespace: str,
    payload: FetchCallSchema,
    run_name: str = const.DEFAULT_FETCH_CALLS_API_RUN
):
    run = call_kfp_method(
        pipeline_func=run_fetch_calls,
        run_name=run_name,
        namespace=namespace,
        arguments=payload.dict()
    )

    return custom_response({
        "message": f"{const.FETCH_CALLS_NAME} pipeline run created successfully.",
        "name": f"{const.FETCH_CALLS_NAME}",
        "run_id": run.run_id,
        "run_url": const.GET_RUN_URL(namespace, run.run_id)
    })
    

@app.post("/{namespace}/pipelines/run/tag-calls/")
def tag_calls_req(
    namespace: str,
    payload: TagCallSchema,
    run_name: str = const.DEFAULT_TAG_CALLS_API_RUN
):
    run = call_kfp_method(
        pipeline_func=run_tag_calls,
        run_name=run_name,
        namespace=namespace,
        arguments=payload.dict()
    )

    return custom_response({
        "message": f"{const.TAG_CALLS_NAME} pipeline run created successfully.",
        "name": f"{const.TAG_CALLS_NAME}",
        "run_id": run.run_id,
        "run_url": const.GET_RUN_URL(namespace, run.run_id)
    })


#TODO: make a response model schema, refactor failures

if __name__ == "__main__":
    app.run(host="0.0.0.0")
