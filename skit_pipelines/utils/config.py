import skit_pipelines.constants as const

from skit_pipelines.pipelines import (
    run_fetch_calls,
    run_tag_calls,
    run_xlmr_train
)

RUN_NAME_MAP = {
    const.FETCH_CALLS_NAME: const.DEFAULT_FETCH_CALLS_API_RUN,
    const.TAG_CALLS_NAME: const.DEFAULT_TAG_CALLS_API_RUN,
    const.TRAIN_XLMR_NAME: const.DEFAULT_XLMR_MODEL_API_RUN
}

PIPELINE_FN_MAP = {
    const.FETCH_CALLS_NAME: run_fetch_calls,
    const.TAG_CALLS_NAME: run_tag_calls,
    const.TRAIN_XLMR_NAME: run_xlmr_train
}

def valid_pipeline(pipeline_name: str) -> bool:
    return pipeline_name in PIPELINE_FN_MAP.keys()
