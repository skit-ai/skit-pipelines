import kfp
import os

from skit_pipelines import constants as pipeline_constants
from skit_pipelines.components import (
    create_features_op,
    create_true_intent_labels_op,
    create_utterances_op,
    download_from_s3_op,
    extract_tgz_op,
    gen_irr_metrics_op,
    get_preds_voicebot_xlmr_op,
    upload2s3_op,
)

UTTERANCES = pipeline_constants.UTTERANCES
INTENT_Y = pipeline_constants.INTENT_Y
BUCKET = pipeline_constants.BUCKET
INTENT_PRED = pipeline_constants.INTENT_PRED


@kfp.dsl.pipeline(
    name="XLMR Voicebot Eval Pipeline",
    description="Produces IRR metrics for an XLM Roberta model on given dataset.",
)
def run_xlmr_eval(*,
    s3_path_data: str,
    s3_path_model: str,
    org_id: str,
    use_state: bool = True,
    model_name: str = "xlm-roberta-base",
):
    
    with kfp.dsl.Condition(s3_path_data != "", "s3_path_data_check") as check1:
        tagged_data_op = download_from_s3_op(storage_path=s3_path_data)
    
    with kfp.dsl.Condition(s3_path_model != "", "s3_path_model_check") as check2:
        loaded_model_op = download_from_s3_op(storage_path=s3_path_model)
        extracted_model_op = extract_tgz_op(loaded_model_op.outputs["output"])
    
    # tagged_data_op = download_from_s3_op(s3_path_data)
    # loaded_model_op = download_from_s3_op(s3_path_model)
    # preprocess the file

    # Create true label column
    # Want (check1 and check2) behavior in after, is this correct?
    preprocess_data_op = create_utterances_op(tagged_data_op.outputs["output"]).after(check1, check2)

    # Create utterance column
    preprocess_data_op = create_true_intent_labels_op(
        preprocess_data_op.outputs["output"]
    )

    #TODO: Create train and test splits - keep only valid utterances

    # Normalize utterance column
    preprocess_data_op = create_features_op(
        preprocess_data_op.outputs["output"], use_state
    )

    model_path = os.path.join(str(extracted_model_op.outputs["output"]),"data")

    #get predictions from the model
    pred_op = get_preds_voicebot_xlmr_op(
        preprocess_data_op.outputs["output"],
        model_path,
        utterance_column=UTTERANCES,
        input_true_label_column=INTENT_Y,
        output_pred_label_column=INTENT_PRED,
    )

    irr_op = gen_irr_metrics_op(
        pred_op.outputs["output"],
        true_label_column=INTENT_Y,
        pred_label_column=INTENT_PRED,
    )
    
    # produce test set metrics.
    upload = upload2s3_op(irr_op.outputs["output"], org_id, "xlmr_irr_metrics", BUCKET, ".txt")
    upload.execution_options.caching_strategy.max_cache_staleness = (
        "P0D"  # disables caching
    )