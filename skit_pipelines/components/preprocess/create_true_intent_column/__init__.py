import kfp
from kfp.components import InputPath, OutputPath

from skit_pipelines import constants as pipeline_constants


def create_intent_labels(data_path: InputPath(str), alias_yaml_path:InputPath(str), output_path: OutputPath(str)):
    import pandas as pd
    from loguru import logger

    from skit_pipelines import constants as pipeline_constants
    from skit_pipelines.components.preprocess.create_true_intent_column.utils import (
        pick_1st_tag,
    )

    def _get_alias_dict_from_alias_yaml_path(path):
        import yaml
        with open(path) as yf:
            y = yaml.safe_load(yf.read())
        if not y:
            # safe_load returns None on passing an empty file.
            return
        alias_dict = {}
        for k, l in y.items():
            for v in l:
                if v in alias_dict:
                    raise ValueError(f"provided alias_yaml has multiple aliasings for {v}")
                alias_dict[v] = k
        return alias_dict

    def _alias_str(s,alias_dict):
        if s not in alias_dict: return "ALIAS_INFO_MISSING"
        return alias_dict[s]

    INTENT_Y = pipeline_constants.INTENT_Y

    train_df = pd.read_csv(data_path)
    train_df[INTENT_Y] = train_df.tag.apply(pick_1st_tag)
    alias_dict = _get_alias_dict_from_alias_yaml_path(alias_yaml_path)
    if alias_dict:
        train_df[INTENT_Y] = train_df[INTENT_Y].apply(_alias_str, args=(alias_dict,))
        train_df = train_df.query(f"{INTENT_Y} != 'ALIAS_INFO_MISSING'")
    logger.debug(train_df[INTENT_Y][:10])

    train_df.to_csv(output_path, index=False)


create_true_intent_labels_op = kfp.components.create_component_from_func(
    create_intent_labels, base_image=pipeline_constants.BASE_IMAGE
)
