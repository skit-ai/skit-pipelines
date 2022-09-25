from kfp.dsl import PipelineConf

import skit_pipelines.constants as const
from skit_pipelines.api import models


def get_pipeline_config_kfp(pipeline_name):
    ## since currently gpu node doesn't support all integrations with db,
    ## we set default pipeline nodeselector to be CPU node
    ## while setting gpu node only for the required component in pipeline.

    # node_type = models.PodNodeSelectorMap[pipeline_name]
    # if node_type == const.CPU_NODE_LABEL:
    return PipelineConf().set_default_pod_node_selector(
        label_name=const.POD_NODE_SELECTOR_LABEL,
        value=const.CPU_NODE_LABEL,  # node_type
    )
