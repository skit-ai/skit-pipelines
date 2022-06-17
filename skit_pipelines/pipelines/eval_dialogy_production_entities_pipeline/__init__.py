import kfp

from skit_pipelines import constants as pipeline_constants
from skit_pipelines.components import (
    gen_err_metrics_op,
    prod_slu_inference_op,
    upload2s3_op,
)


@kfp.dsl.pipeline(
    name="Dialogy Production SLU Inference Entity Pipeline",
    description="On a given tagged dataset, slu repo docker image and does inference for entities.",
)
def dialogy_prod_infer_and_eval_entities(
    *,
    s3_tagged_data_path: str,
    slu_image_on_ecr: str,
    lang: str,
    org_id: str,
    use_existing_prediction: bool = True,
    use_duckling: bool = False,
):
    """ """

    prod_slu_infer_op = prod_slu_inference_op(
        s3_tagged_data_path,
        slu_image_on_ecr=slu_image_on_ecr,
        lang=lang,
        use_existing_prediction=use_existing_prediction,
        use_duckling=use_duckling,
    )

    prod_slu_infer_op.execution_options.caching_strategy.max_cache_staleness = (
        "P0D"  # disables caching
    )

    prod_slu_infer_op.set_gpu_limit(1)

    err_op = gen_err_metrics_op(
        prod_slu_infer_op.outputs["output"],
        true_label_column="true_entities",
        pred_label_column="pred_entities",
    )

    # produce test set metrics.
    upload_err = upload2s3_op(
        path_on_disk=err_op.outputs["output"],
        reference=org_id,
        file_type="xlmr-dialogy-err-metrics",
        bucket=pipeline_constants.BUCKET,
        ext=".csv",
    )
    upload_err.execution_options.caching_strategy.max_cache_staleness = (
        "P0D"  # disables caching
    )


__all__ = ["dialogy_prod_infer_and_eval_entities"]
