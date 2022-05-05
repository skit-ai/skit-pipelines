import kfp

from skit_pipelines import constants as pipeline_constants
from skit_pipelines.components import (
    create_features_op,
    create_true_intent_labels_op,
    create_utterances_op,
    download_from_s3_op,
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
    description="Produces IRR numbers for an XLM Roberta model on given dataset.",
)
def run_xlmr_eval(
    s3_path_data: str,
    s3_path_model: str,
    org_id: int,
    use_state: bool = True,
    model_name: str = "xlm-roberta-base",
    max_seq_length: int = 128,
):
    tagged_data_op = download_from_s3_op(s3_path_data)
    loaded_model_op = download_from_s3_op(s3_path_model)
    # preprocess the file

    # Create true label column
    preprocess_data_op = create_utterances_op(tagged_data_op.outputs["output"])

    # Create utterance column
    preprocess_data_op = create_true_intent_labels_op(
        preprocess_data_op.outputs["output"]
    )

    #TODO: Create train and test splits - keep only valid utterances

    # Normalize utterance column
    preprocess_data_op = create_features_op(
        preprocess_data_op.outputs["output"], use_state
    )

    #get predictions from the model
    pred_op = get_preds_voicebot_xlmr_op(
        data_path=preprocess_data_op.outputs["output"],
        model_path=loaded_model_op.outputs["output"],
        utterance_column=UTTERANCES,
        input_true_label_column=INTENT_Y,
        output_pred_label_column=INTENT_PRED,
    )

    irr_op = gen_irr_metrics_op(
        data_path=pred_op.outputs["output"],
        true_label_column=INTENT_Y,
        pred_label_column=INTENT_PRED,
    )
    
    # produce test set metrics.
    upload2s3_op(irr_op.outputs["output"], org_id, "xlmr_irr_metrics", BUCKET, ".txt")
