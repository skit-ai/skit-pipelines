import kfp

from kubernetes import client as k8s_client
from kubernetes.client.models import V1EnvVar, V1ContainerPort, V1PodSpec, V1Container

from skit_pipelines import constants as pipeline_constants
from skit_pipelines.components import (
    gen_err_metrics_op,
    upload2s3_op,
    # prod_slu_inference_op,
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

    ## method 1
    # prod_slu_infer_op = (
    #     prod_slu_inference_op(
    #         s3_tagged_data_path,
    #         slu_image_on_ecr=slu_image_on_ecr,
    #         lang=lang,
    #         use_existing_prediction=use_existing_prediction,
    #         use_duckling=use_duckling,
    #     ).add_volume(
    #         k8s_client.V1Volume(
    #             name="docker-socket",
    #             host_path=k8s_client.V1HostPathVolumeSource(
    #                 path="/var/run/docker.sock"
    #             ),
    #         )
    #     )
    #     .add_volume_mount(
    #         k8s_client.V1VolumeMount(
    #             name="docker-socket", mount_path="/var/run/docker.sock"
    #         )
    #     ).container.add_container_kwargs(
    #         V1NetworkPolicy(kind="host")
    #     )
    # )

    ## method 3
    # inference_container = V1Container(
    #         name="prod_inference_container",
    #         image=pipeline_constants.BASE_IMAGE,
    #         command=["python", "/home/kfp/skit_pipelines/components/prod_slu_inference_for_entities.py"],
    #         arguments=[
    #             "--s3_tagged_data_path", s3_tagged_data_path,
    #             "--output_path", inference_csv_file_path,   
    #             "--slu_image_on_ecr", slu_image_on_ecr,
    #             "--lang", lang,
    #             "--use_existing_prediction", use_existing_prediction,
    #             "--use_duckling", use_duckling,
    #         ],
    #         volume_mounts=k8s_client.V1VolumeMount(name="docker-socket", mount_path="/var/run/docker.sock"),
    #     )
    # inference_pod_spec = V1PodSpec(
    #     container=[inference_container]
    #     host_network=True,
    #     volumes=k8s_client.V1Volume(name="docker-socket", host_path=k8s_client.V1HostPathVolumeSource(path="/var/run/docker.sock")),
    # )

    ## method 3
    inference_csv_file_path = "/dialogy_entities_inference.csv"
    prod_slu_infer_op = kfp.dsl.ContainerOp(
        name="prod_slu_infer_op",
        image=pipeline_constants.BASE_IMAGE,
        command=["python", "/home/kfp/skit_pipelines/components/prod_slu_inference_for_entities.py"],
        arguments=[
            "--s3_tagged_data_path", s3_tagged_data_path,
            "--output_path", inference_csv_file_path,   
            "--slu_image_on_ecr", slu_image_on_ecr,
            "--lang", lang,
            "--use_existing_prediction", use_existing_prediction,
            "--use_duckling", use_duckling,
        ],
        container_kwargs={"ports": [V1ContainerPort(container_port=9002, host_port=9002), V1ContainerPort(container_port=8000, host_port=8000)]},
        file_outputs={"output": inference_csv_file_path}
    ).add_volume(
            k8s_client.V1Volume(
                name="docker-socket",
                host_path=k8s_client.V1HostPathVolumeSource(
                    path="/var/run/docker.sock"
                ),
            )
        ).add_volume_mount(
            k8s_client.V1VolumeMount(
                name="docker-socket", mount_path="/var/run/docker.sock"
            )
        )

    prod_slu_infer_op.execution_options.caching_strategy.max_cache_staleness = (
        "P0D"  # disables caching
    )

    # prod_slu_infer_op.set_gpu_limit(1)

    err_op = gen_err_metrics_op(
        prod_slu_infer_op.outputs["output"],
        true_label_column="true_entities",
        pred_label_column="pred_entities",
    )

    # produce test set metrics.
    upload_err = upload2s3_op(
        path_on_disk=err_op.outputs["entity_report"],
        reference=org_id,
        file_type="xlmr-dialogy-err-metrics",
        bucket=pipeline_constants.BUCKET,
        ext=".csv",
    )
    upload_err.execution_options.caching_strategy.max_cache_staleness = (
        "P0D"  # disables caching
    )


__all__ = ["dialogy_prod_infer_and_eval_entities"]


# if __name__ == "__main__":

#     kfp.run_pipeline_func_locally(
#         dialogy_prod_infer_and_eval_entities,
#         arguments={
#             "s3_tagged_data_path": "s3://vernacular-ml/project/129_3861/2022-06-14/129_3861-2022-06-14-tagged.csv",
#             "slu_image_on_ecr": "536612919621.dkr.ecr.ap-south-1.amazonaws.com/vernacular-voice-services/ai/clients/ashley:master",
#             "lang": "en",
#             "org_id": "129",
#             "use_duckling": "True",
#         }
#         )

