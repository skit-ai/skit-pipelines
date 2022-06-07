import kfp

from skit_pipelines.components import (
    download_repo_from_gitlab_op,
    prod_slu_inference_op,
)


@kfp.dsl.pipeline(
    name="Dialogy Production SLU Inference Pipeline",
    description="On a given tagged dataset, clones gitlab prod slu repo by project ID and does inference.",
)
def dialogy_prod_infer_and_eval(
    *,
    gitlab_project_id: int,
    s3_tagged_data_path: str,
):
    """
    """


    gitlab_clone_op = download_repo_from_gitlab_op(gitlab_project_id)
    prod_slu_infer_op = prod_slu_inference_op(
        slu_repo_tar_path=gitlab_clone_op.outputs["target_path"],
        s3_tagged_data_path=s3_tagged_data_path,
        project_id=gitlab_project_id,
    )

    gitlab_clone_op.execution_options.caching_strategy.max_cache_staleness = (
        "P0D"  # disables caching
    )

    prod_slu_infer_op.execution_options.caching_strategy.max_cache_staleness = (
        "P0D"  # disables caching
    )

    prod_slu_infer_op.set_gpu_limit(1)


    # # produce test set metrics.
    # upload_irr = upload2s3_op(
    #     path_on_disk=irr_op.outputs["output"],
    #     reference=org_id,
    #     file_type="xlmr-irr-metrics",
    #     bucket=BUCKET,
    #     ext=".txt"
    # )
    # upload_irr.execution_options.caching_strategy.max_cache_staleness = (
    #     "P0D"  # disables caching
    # )



__all__ = ["dialogy_prod_infer_and_eval"]
