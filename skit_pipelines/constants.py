import os

ECR_REGISTRY = os.environ["ECR_REGISTRY"]
REGION = os.environ["REGION"]
BASE_IMAGE = os.environ["BASE_IMAGE"]
CUDA_IMAGE = os.environ["CUDA_IMAGE"]
US_EAST_1 = "us-east-1"
AP_SOUTH_1 = "ap-south-1"
TIMEZONE = "Asia/Kolkata" if REGION == AP_SOUTH_1 else "America/New_York"
KALDI_REPOSITORY = "vernacular-voice-services/voice-services/kaldi-nvidia-lm-tuning"
KALDI_IMAGE = f"{ECR_REGISTRY}/{KALDI_REPOSITORY}:latest"
BUCKET = os.environ["BUCKET"]
SLACK_TOKEN = os.environ["SLACK_TOKEN"]
SLACK_SIGNING_SECRET = os.environ["SLACK_SIGNING_SECRET"]
DEFAULT_CHANNEL = os.environ["DEFAULT_SLACK_CHANNEL"]

CONSOLE_API_URL = os.environ["SKIT_API_GATEWAY_URL"]
CONSOLE_IAM_EMAIL = os.environ["SKIT_API_GATEWAY_EMAIL"]
CONSOLE_IAM_PASSWORD = os.environ["SKIT_API_GATEWAY_PASSWORD"]

# console base URL, for call report purposes
CONSOLE_URL = (
    "https://console.skit.ai"
    if REGION == AP_SOUTH_1
    else "https://console.us.skit.ai"
)

# logic for getting the correct URL for the audio files based on region
USE_FSM_URL = False if REGION == AP_SOUTH_1 else True

AUDIO_URL_DOMAIN = os.environ["AUDIO_URL_DOMAIN"]

# for fsm-db
DB_HOST = os.environ["DB_HOST"]
DB_PORT = os.environ["DB_PORT"]
DB_PASSWORD = os.environ["DB_PASSWORD"]
DB_USER = os.environ["DB_USER"]

# for metrics-db
ML_METRICS_DB_NAME = os.environ["ML_METRICS_DB_NAME"]
ML_METRICS_DB_HOST = os.environ["ML_METRICS_DB_HOST"]
ML_METRICS_DB_PORT = os.environ["ML_METRICS_DB_PORT"]
ML_METRICS_DB_USER = os.environ["ML_METRICS_DB_USER"]
ML_METRICS_DB_PASSWORD = os.environ["ML_METRICS_DB_PASSWORD"]

KF_NAMESPACE = "skit"
DEFAULT_EXPERIMENT_NAME = "Default"

PROJECT_NAME = "skit-pipelines"
CONFIG_DIR = "config/"
CONFIG_FILE = "config.yaml"
CONFIG_FILE_PATH = os.path.join(CONFIG_DIR, CONFIG_FILE)
KAFKA_INSTANCE = os.environ.get("KAFKA_INSTANCE", "kafka:9092")

VOICE_BOT_XLMR_LABEL_COL = ""
TEXT = "text"

TRAIN = "train"
TEST = "test"
LABELS = "labels"
CSV_FILE = ".csv"
WAV_FILE = ".wav"
UTTERANCES = "utterances"
ALTERNATIVES = "alternatives"
TAG = "tag"
ID = "id"
DATA_ID = "data_id"
INTENT_X = "intent_x"
INTENT_Y = "intent_y"
TRANSCRIPT_Y = "transcript_y"
INTENT = "intent"
STATE = "state"
DATA = "data"
OLD_DATA = "old_data"

START_TOKEN = "<s>"
END_TOKEN = "</s>"
TRANSCRIPT = "transcript"

MULTI_USER = "multi_user"
KFP_RUN_FN = "create_run_from_pipeline_func"


KF_USERNAME = os.environ["KF_USERNAME"]
KF_PASSWORD = os.environ["KF_PASSWORD"]

JWT_SECRET_KEY = os.environ["JWT_SECRET_KEY"]

USERNAME_ELEMENT_ID = "signInFormUsername"
PASSWORD_ELEMENT_ID = "signInFormPassword"
SUBMIT_BUTTON_ID = "signInSubmitButton"

USERNAME_XPATH = f"(//input[@id='{USERNAME_ELEMENT_ID}'])[2]"
PASSWORD_XPATH = f"(//input[@id='{PASSWORD_ELEMENT_ID}'])[2]"
SUBMIT_XPATH = f"(//input[@name='{SUBMIT_BUTTON_ID}'])[2]"

NODE_TYPE = "type"
NODE_TYPE_POD = "Pod"
NODE_OUTPUT = "outputs"
NODE_ARTIFACTS = "artifacts"
ARTIFACT_URI_KEY = "key"
OBJECT_BUCKET = "bucket"
NODE_PHASE = "phase"

NAME = "name"
VALUE = "value"
DOMAIN = "domain"
COOKIES_PATH = "/tmp/kf_cookies.json"
ACCESS_TOKEN_PATH = "/tmp/kfp_server_token.json"
KUBEFLOW_GATEWAY_ENDPOINT = os.environ["KUBEFLOW_GATEWAY_ENDPOINT"]
KUBEFLOW_BUCKET = "kubeflow-skit" if REGION == AP_SOUTH_1 else "kubeflow-us-cluster"
COOKIE_0 = "AWSELBAuthSessionCookie-0"
COOKIE_1 = "AWSELBAuthSessionCookie-1"
COOKIE_DICT = {COOKIE_0: None, COOKIE_1: None}
PIPELINE_HOST_URL = f"https://{KUBEFLOW_GATEWAY_ENDPOINT}/pipeline"
LABELSTUDIO_SVC = (
    "https://labelstudio.skit.ai"
    if REGION == AP_SOUTH_1
    else "https://labelstudio.us.skit.ai"
)
LABELSTUDIO_TOKEN = os.environ["LABELSTUDIO_TOKEN"]


def CONSTRUCT_COOKIE_TOKEN(cookie_dict):
    return (
        f"{COOKIE_0}={cookie_dict.get(COOKIE_0)};{COOKIE_1}={cookie_dict.get(COOKIE_1)}"
    )


def GET_RUN_URL(namespace, id):
    return f"{PIPELINE_HOST_URL}/?ns={namespace}#/runs/details/{id}"


FILTER_LIST = [
    "webhook_uri",
]

REFERENCE_URL = "https://metabase.skit.ai/question/2403-tagged-data?job_id="
# for pushing eevee intent metrics to intent_metrics table.
ML_INTENT_METRICS_INSERT_SQL_QUERY = """
INSERT INTO intent_metrics 
(
    slu_name,
    dataset_job_id,
    language,
    metric_name,
    n_calls,
    n_turns,
    precision,
    recall,
    f1,
    support,
    created_at,  
    calls_from_date,
    calls_to_date,
    tagged_from_date,
    tagged_to_date,
    reference_url,
    raw
)
VALUES
(
    %(slu_name)s,
    %(dataset_job_id)s,
    %(language)s,
    %(metric_name)s,
    %(n_calls)s,
    %(n_turns)s,
    %(precision)s,
    %(recall)s,
    %(f1)s,
    %(support)s,
    %(created_at)s,  
    %(calls_from_date)s,
    %(calls_to_date)s,
    %(tagged_from_date)s,
    %(tagged_to_date)s,
    %(reference_url)s,
    %(raw)s
)
"""

# for pushing eevee entity metrics to entity_metrics table.
ML_ENTITY_METRICS_INSERT_SQL_QUERY = """
INSERT INTO entity_metrics 
(
    slu_name,
    dataset_job_id,
    language,
    metric_name,
    n_calls,
    n_turns,
    false_positive_rate,
    false_negative_rate,
    mismatch_rate,
    support,
    negatives,
    created_at,  
    calls_from_date,
    calls_to_date,
    tagged_from_date,
    tagged_to_date,
    raw
)
VALUES
(
    %(slu_name)s,
    %(dataset_job_id)s,
    %(language)s,
    %(metric_name)s,
    %(n_calls)s,
    %(n_turns)s,
    %(false_positive_rate)s,
    %(false_negative_rate)s,
    %(mismatch_rate)s,
    %(support)s,
    %(negatives)s,
    %(created_at)s,  
    %(calls_from_date)s,
    %(calls_to_date)s,
    %(tagged_from_date)s,
    %(tagged_to_date)s,
    %(raw)s
)
"""

PERSONAL_ACCESS_TOKEN_GITHUB = os.environ["PERSONAL_ACCESS_TOKEN_GITHUB"]
EEVEE_RAW_FILE_GITHUB_REPO_URL = (
    "https://raw.githubusercontent.com/skit-ai/eevee-yamls/main/"
)

DUCKLING_HOST = os.environ["DUCKLING_HOST"]

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

# K8s
POD_NODE_SELECTOR_LABEL = "beta.kubernetes.io/instance-type"
CPU_NODE_LABEL = "m5.xlarge" if REGION == AP_SOUTH_1 else "r6i.2xlarge"
GPU_NODE_LABEL = "g4dn.xlarge"

# Bots
SLACK_BOT_NAME = "charon" if REGION == AP_SOUTH_1 else "charon-us"

# VCS
GITLAB = "gitlab.com"
GITLAB_API_BASE = f"https://{GITLAB}/api/v4/projects/"
GITLAB_SLU_PROJECT_PATH = "skit-ai/slu"
GITLAB_USER = "automation"
GITLAB_USER_EMAIL = "automation@skit.ai"
GITLAB_PRIVATE_TOKEN = os.environ["PERSONAL_ACCESS_TOKEN_GITLAB"]


def GET_GITLAB_REPO_URL(
    repo_name: str, project_path: str, user: str, token: str
) -> str:
    return f"https://{user}:{token}@{GITLAB}/{project_path}/{repo_name}.git"


GITHUB = "github.com"


CLASSIFICATION_REPORT = "classification_report"
FULL_CONFUSION_MATRIX = "full_confusion_matrix"

GET_ANNOTATIONS_LABEL_STORE = "pipeline_secrets/get_annotations_label_store.sql"
GET_CALL_CONTEXT_LABEL_STORE = "pipeline_secrets/get_call_context_label_store.sql"
LABEL_STUDIO_DB_NAME = "label_studio"
WAREHOUSE_DB_NAME = "warehouse"
SQL_RANDOM_SEED = 0.5
DATA_LABEL_DEFAULT = "Live"
