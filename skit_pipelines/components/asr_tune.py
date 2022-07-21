import kfp
from kfp.components import InputPath

from skit_pipelines import constants as pipeline_constants


def asr_tune(
    corpus_path: InputPath(str),
    augment_wordlist_path: InputPath(str),
    remove_wordlist_path: InputPath(str),
    lang: str,
    base_model_path: str,
    target_model_path: str,
    domain_bias: float,
    ) -> None:
    import tuning.app.core as tuning_core

    from loguru import logger

    tuning_core.bias_lm(language=lang,base_model_uri=base_model_path,domain_bias=domain_bias, target_model_uri=target_model_path,corpus_path=corpus_path,augment_wordlist=augment_wordlist_path,remove_wordlist=remove_wordlist_path)


asr_tune_op = kfp.components.create_component_from_func(
    asr_tune, base_image=pipeline_constants.BASE_IMAGE
)
