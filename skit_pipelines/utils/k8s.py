from kfp.dsl import PipelineConf

import skit_pipelines.constants as const
from skit_pipelines.api import models


def get_pipeline_config_kfp(pipeline_name):
    node_type = models.PodNodeSelectorMap[pipeline_name]
    if node_type == const.CPU_NODE_LABEL:
        return PipelineConf().set_default_pod_node_selector(
            label_name=const.POD_NODE_SELECTOR_LABEL, value=node_type
        )
