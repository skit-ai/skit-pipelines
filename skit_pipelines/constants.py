import os

BASE_IMAGE = os.environ["BASE_IMAGE"]
CUDA_P38_IMAGE = os.environ["CUDA_IMAGE"]
BUCKET = os.environ["BUCKET"]
SLACK_TOKEN = os.environ["SLACK_TOKEN"]
SLACK_SIGNING_SECRET = os.environ["SLACK_SIGNING_SECRET"]
DEFAULT_CHANNEL = os.environ["DEFAULT_SLACK_CHANNEL"]

CONSOLE_API_URL = os.environ["SKIT_API_GATEWAY_URL"]
CONSOLE_IAM_EMAIL = os.environ["SKIT_API_GATEWAY_EMAIL"]
CONSOLE_IAM_PASSWORD = os.environ["SKIT_API_GATEWAY_PASSWORD"]

# for fsm-db
DB_HOST = "production-postgresql-slave.default"
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
UTTERANCES = "utterances"
ALTERNATIVES = "alternatives"
TAG = "tag"
ID = "id"
DATA_ID = "data_id"
INTENT_X = "intent_x"
INTENT_Y = "intent_y"
INTENT = "intent"
STATE = "state"

START_TOKEN = "<s>"
END_TOKEN = "</s>"
TRANSCRIPT = "transcript"

MULTI_USER = "multi_user"
KFP_RUN_FN = "create_run_from_pipeline_func"


KF_USERNAME = os.environ["KF_USERNAME"]
KF_PASSWORD = os.environ["KF_PASSWORD"]

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

NAME = "name"
VALUE = "value"
DOMAIN = "domain"
COOKIES_PATH = "/tmp/kf_cookies.json"
KUBEFLOW_GATEWAY_ENDPOINT = os.environ["KUBEFLOW_GATEWAY_ENDPOINT"]
COOKIE_0 = "AWSELBAuthSessionCookie-0"
COOKIE_1 = "AWSELBAuthSessionCookie-1"
COOKIE_DICT = {COOKIE_0: None, COOKIE_1: None}
PIPELINE_HOST_URL = f"https://{KUBEFLOW_GATEWAY_ENDPOINT}/pipeline"
LABELSTUDIO_SVC = "https://labelstudio.skit.ai"
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
