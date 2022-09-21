import kfp
from kfp.components import InputPath, OutputPath

from skit_pipelines import constants as pipeline_constants


def asr_tune(
    corpus_path: InputPath(str),
    val_corpus_path: InputPath(str),
    augment_wordlist_path: InputPath(str),
    remove_wordlist_path: InputPath(str),
    base_model_path: InputPath(str),
    general_lm_path: InputPath(str),
    output_path: OutputPath(str),
    lang: str,
) -> None:
    def exec_shell(cmd: str, tolerant: bool = False):
        import subprocess
        import sys

        print(f"executing: {cmd}", file=sys.stdout)
        code = subprocess.call(
            "source ~/.bashrc && " + cmd,
            shell=True,
            executable="/bin/bash",
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        if code:
            if not tolerant:
                raise Exception(f"command {cmd} failed with non-zero code: {code}")
            else:
                print(f"return code: {code}, but tolerant is set as {tolerant}")

    BASE_PATH = "~"
    RECIPE = "s3"
    LANGS = {"en": "english", "hi": "hindi"}
    PHONEMIZERS = {
        "en": "models/models36/en_with_hindi_phones/en-hi-ipa-model",
        "hi": "~/unified-parser/unified-parser",
    }
    NNET_SUFFIX = {"en": "1a", "hi": "1a"}

    exec_shell(
        f"wget https://repo.anaconda.com/miniconda/Miniconda3-py37_4.12.0-Linux-x86_64.sh && bash Miniconda3-py37_4.12.0-Linux-x86_64.sh -b"
    )
    exec_shell("echo 'export KALDI_ROOT=/opt/kaldi/' >> ~/.bashrc")
    exec_shell("echo 'source ~/kaldi/recipes/s3/path.sh' >> ~/.bashrc")

    exec_shell("echo 'export PATH=/root/miniconda3/bin/:$PATH' >> ~/.bashrc")
    exec_shell(
        "echo 'export PYTHONIOENCODING=utf8 && export LC_ALL=C.UTF-8 && export LANG=C.UTF-8' >> ~/.bashrc"
    )
    exec_shell("conda init bash")
    exec_shell("conda create -n condaenv python=3.6.5")
    exec_shell("echo 'conda activate condaenv' >> ~/.bashrc")
    exec_shell("echo $PATH")
    # exec_shell("conda install python=3.6")
    exec_shell("conda install -n condaenv git pip")

    exec_shell("python --version")
    exec_shell("python3 --version")
    exec_shell("pip --version")
    exec_shell("pip3 --version")

    exec_shell("pip install poetry==1.1.13")
    exec_shell("which poetry")
    exec_shell("pip install setuptools==58")

    # __clone_kaldi
    exec_shell(f"cd {BASE_PATH}/kaldi && git pull")
    exec_shell(f"cd {BASE_PATH}/kaldi && pip install -r requirements.txt")
    # __clone_corprep
    exec_shell(f"cd {BASE_PATH}/corprep && poetry install")
    exec_shell(f"cd {BASE_PATH}/corprep && poetry run pip3 install -U nltk")

    exec_shell(f"cd {BASE_PATH}/g2p && poetry install")

    # NOTE: might need to run all the `__setup` things here.
    exec_shell(f"mkdir -p {BASE_PATH}/data")
    exec_shell(f"cp {corpus_path} {BASE_PATH}/data/corpus.txt")
    exec_shell(f"cp {val_corpus_path} {BASE_PATH}/data/corpus.val.txt")

    exec_shell(f"cp {augment_wordlist_path} {BASE_PATH}/data/vocab.augment.txt")
    exec_shell(f"cp {remove_wordlist_path} {BASE_PATH}/data/vocab.remove.txt")

    exec_shell(f"cp -R {base_model_path} {BASE_PATH}/model")
    exec_shell(f"cp {general_lm_path} {BASE_PATH}/data/lm_general.arpa")
    recipe_path = f"{BASE_PATH}/kaldi/recipes/{RECIPE}"
    exec_shell(f"mv {BASE_PATH}/model/exp {recipe_path}/exp")
    exec_shell(f"mv {BASE_PATH}/model/data {recipe_path}/data")
    exec_shell(f"mv {BASE_PATH}/data/* {recipe_path}/data/local/")
    exec_shell(f"ls -lat {recipe_path}/data/local/")

    exec_shell(
        f"cd ~/corprep && python ~/kaldi/scripts/corpus/fix_corpus.py ~/corprep/data/processed/{LANGS[lang]}.yaml {recipe_path}/data/local/corpus.txt"
    )
    exec_shell(
        f"cd ~/corprep && poetry run python ~/kaldi/scripts/corpus/fix_corpus.py ~/corprep/data/processed/{LANGS[lang]}.yaml {recipe_path}/data/local/corpus.val.txt"
    )
    exec_shell(
        f"cd {recipe_path}/data/local/ && python3 ~/kaldi/scripts/corpus/uniq_words.py corpus.txt"
    )
    exec_shell(f"cd {recipe_path}/data/local/ && mv corpus.words.txt vocab.txt")

    # process the augment wordlist
    augment_wordlist = f"vocab.txt"
    exec_shell(f"cd ~/kaldi && pip3 install -r requirements.txt")
    exec_shell(
        f"cd {recipe_path}/data/local && less dict/lexicon.txt | grep -v '<SIL>' | grep -v '<UNK>' > dict/lexicon_filt.txt"
    )
    exec_shell(
        f"cd {recipe_path}/data/local && python3 ~/kaldi/scripts/lexicon/lexicon_txt_to_csv.py dict/lexicon_filt.txt"
    )
    exec_shell(
        f"cd {recipe_path}/data/local && cp dict/lexicon_filt.csv dict/lexicon.csv"
    )

    # exec_shell(f"cd {BASE_PATH}/g2p && poetry install")

    if lang == "en":
        # generate phonemes
        exec_shell(f"mkdir -p {recipe_path}/data/local/lexicons")
        exec_shell(f"cd ~/g2p && poetry run pip3 install -r ~/kaldi/requirements.txt")
        exec_shell(
            f"cd ~/g2p && poetry run python3 ~/kaldi/scripts/lexicon/words_to_lexicon.py {recipe_path}/data/local/{augment_wordlist} {recipe_path}/data/local/lexicons/lexicon.csv --sequitur-model {PHONEMIZERS[lang]}"
        )
    elif lang == "hi":
        exec_shell(f"mkdir -p {recipe_path}/data/local/lexicons")
        exec_shell(f"cd ~/g2p && pip3 install -r ~/kaldi/requirements.txt")
        exec_shell(
            f"cd ~/g2p && poetry run python3 ~/kaldi/scripts/lexicon/words_to_lexicon.py {recipe_path}/data/local/{augment_wordlist} {recipe_path}/data/local/lexicons/ext.lexicon.csv --unified-parser {PHONEMIZERS[lang]}"
        )
    else:
        raise UserWarning("language specified does not have phonemization configured")
    exec_shell(
        f"cd {recipe_path}/data/local && cp dict/lexicon.csv lexicons/orig.lexicon.csv"
    )
    exec_shell(
        f"cd {recipe_path}/data/local && python3 ~/kaldi/scripts/lexicon/merge_lexicons.py lexicons lexicon_ext.csv"
    )

    # process the remove wordlist
    lexicon_path = f"lexicon_ext.csv"
    exec_shell(f"cd {recipe_path}/data/local && cp {lexicon_path} tmp_lexicon.csv")
    exec_shell(
        f"cd {recipe_path}/data/local && python ~/kaldi/scripts/lexicon/remove_words.py --inplace tmp_lexicon.csv {remove_wordlist_path}"
    )
    exec_shell(f"cd {recipe_path}/data/local && cp -nf tmp_lexicon.csv lexicon_ext.csv")

    dict_dir = f"dict_ext"
    exec_shell(f"cd {recipe_path}/data/local")
    exec_shell(
        f"cd {recipe_path}/data/local && python3 ~/kaldi/scripts/lexicon/lexicon_csv_to_txt.py lexicon_ext.csv"
    )
    exec_shell(f"cd ~/kaldi")
    exec_shell(f"mkdir -p {recipe_path}/data/local/{dict_dir}")
    exec_shell(
        f'cd ~/kaldi && python3 -c "import scripts.artefacts.prepare_dict as prep; prep.gen_phones(\\"recipes/{RECIPE}/data/local/lexicon_ext.txt\\",\\"recipes/{RECIPE}\\",dict=\\"{dict_dir}\\")"'
    )

    exec_shell(f"cd {recipe_path}")
    exec_shell(
        f"cd {recipe_path} && cp data/local/corpus.txt data/local/corpus_ext.txt"
    )
    exec_shell(
        f"mkdir ~/kaldi/tools/extras/ && cp ~/kaldi/extras/install_liblbfgs.sh ~/kaldi/tools/extras/"
    )
    exec_shell(
        f"cd ~/kaldi/tools && ./install_srilm.sh somename someorg someuser@somedomain.com"
    )
    exec_shell("echo 'source ~/kaldi/tools/env.sh' >> ~/.bashrc")
    exec_shell(
        "apt update && apt install -y libatlas-base-dev && apt install -y bsdutils && apt install -y bsdmainutils"
    )
    exec_shell(f"ls {recipe_path}/data/local/lm_general.arpa", tolerant=True)
    exec_shell(
        f"ls -lat {recipe_path}/data/local/tmp_general_100k/lm_general.arpa",
        tolerant=True,
    )
    exec_shell(f"ls -lat {recipe_path}/data/local/tmp_ext/lm.arpa", tolerant=True)
    exec_shell(
        f"ls -lat {recipe_path}/data/local/tmp_domain_ext/lm.arpa", tolerant=True
    )
    exec_shell(f"ls -lat {recipe_path}/data/local/tmp_ext/", tolerant=True)
    exec_shell(
        f"cd {recipe_path} && ./lm/tune_lm_domain.sh --mode ext --val-text corpus.val.txt --general-lm data/local/lm_general.arpa"
    )

    # recipe_path = f"~/kaldi/recipes/{RECIPE}"

    # graph creation: Creates final HCLG.fst graph (with new L,G.fst)
    exec_shell(f"cd {recipe_path}")
    exec_shell(
        f'cd {recipe_path} && ./scripts/run_test.sh --create-hclg true --test-sets "" --lang lang_ext --graph-dir graph_ext'
    )

    # model_upload_task = Task(cmd=[
    exec_shell(f"cd ~/kaldi")

    # move final model to output_path
    target_uri = "s3://dummy_bucket/dummy_path".replace("s3://", "")
    # need to run the model_to_bucket.sh script as it prepares the model for uploading.
    exec_shell(
        f"cd ~/kaldi && ./scripts/model_to_bucket.sh recipes/{RECIPE} ext tdnn{NNET_SUFFIX[lang]}_sp_online tree_a_sp AWS {target_uri}",
        tolerant=True,
    )
    exec_shell(f"cd ~/kaldi && mv {recipe_path}/model {output_path}")


asr_tune_op = kfp.components.create_component_from_func(
    asr_tune, base_image=pipeline_constants.KALDI_IMAGE
)
