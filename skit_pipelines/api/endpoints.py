import kfp
import kfp_server_api
from loguru import logger
from fastapi.responses import JSONResponse

from skit_pipelines.api import app, FetchCallSchema, ParseRunResponse
from skit_pipelines.api.custom_responses import basic_response, custom_response
from skit_pipelines.pipelines import run_fetch_calls
from skit_pipelines.utils import kubeflow_login
import skit_pipelines.constants as const


KF_CLIENT: kfp.Client


async def create_pipeline_run(method_fn: str = "create_run_from_pipeline_func", *args, **kwargs):
    global KF_CLIENT
    try:
        client_run = getattr(KF_CLIENT, method_fn)(*args, **kwargs)
    except kfp_server_api.ApiException:
        try:
            KF_CLIENT = await kubeflow_login(force=True)
            client_run = getattr(KF_CLIENT, method_fn)(*args, **kwargs)
        except kfp_server_api.ApiException as e:
            logger.error(f"{e}")
            return custom_response(
                status_code=500,
                message=f"{e}",
                status="error",
            )
    return client_run


@app.on_event("startup")
async def startup_event():
    logger.info("Starting Up...")
    logger.info("Initializing kubeflow client.")
    global KF_CLIENT
    KF_CLIENT = await kubeflow_login()
    logger.info("Kubeflow client initialized.")


@app.get("/")
async def health_check():
    """
    Get server status health.
    The purpose of this API is to help other people/machines know liveness of the application.
    """

    return basic_response("Kubeflow pipeline server is up.")


@app.post("/{namespace}/pipelines/run/fetch-calls/")
async def fetch_calls_req(
    namespace: str,
    payload: FetchCallSchema,
    run_name: str = const.DEFAULT_FETCH_CALLS_API_RUN
):
    run_resp = await create_pipeline_run(
        pipeline_func=run_fetch_calls,
        run_name=run_name,
        namespace=namespace,
        arguments=payload.dict()
    )
    if isinstance(run_resp, JSONResponse):
        return run_resp
    
    completed_resp = run_resp.wait_for_run_completion()
    parsed_resp = ParseRunResponse(run=completed_resp, component_display_name=const.FETCH_CALLS_NAME)
    return custom_response({
        "message": "Run completed successfully.",
        "run_url": parsed_resp.url,
        "file_path": parsed_resp.data_path,
        "s3_path": parsed_resp.s3_uri
    })
    


if __name__ == "__main__":
    app.run(host="0.0.0.0")
