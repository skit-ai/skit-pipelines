import kfp
from kfp.components import InputPath, OutputPath

from skit_pipelines import constants as pipeline_constants


def modify_entity_tog_dataset(
    data_path: InputPath(str),
    output_path: OutputPath(str),
    timezone: str = "Asia/Kolkata"
):
    """
    Takes a tog entity dataset and,
    1) hits duckling service for inference on ground-truth
    2) modifies the predicted entity structure to be consistent
    """


    import pandas as pd
    from loguru import logger

    from skit_pipelines import constants as pipeline_constants
    from skit_pipelines.components import modify_entities

    df = pd.read_csv(data_path)

    logger.info(f"duckling running at: {pipeline_constants.DUCKLING_HOST}")

    mod_df = modify_entities.modify_truth(df, timezone)
    mod_df = modify_entities.modify_predictions(mod_df)
    mod_df.to_csv(output_path, index=False)


modify_entity_tog_dataset_op = kfp.components.create_component_from_func(
    modify_entity_tog_dataset, base_image=pipeline_constants.BASE_IMAGE
)


# if __name__ == "__main__":

#     modify_entity_tog_dataset("4284.csv", "duck_4284.csv")
