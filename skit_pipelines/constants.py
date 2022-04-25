import os

BASE_IMAGE = os.environ["BASE_IMAGE"]
BUCKET = os.environ["BUCKET"]
SLACK_TOKEN = os.environ["SLACK_TOKEN"]
DEFAULT_CHANNEL = os.environ["DEFAULT_SLACK_CHANNEL"]

CONSOLE_API_URL = os.environ["SKIT_API_GATEWAY_URL"]
CONSOLE_IAM_EMAIL = os.environ["SKIT_API_GATEWAY_EMAIL"]
CONSOLE_IAM_PASSWORD = os.environ["SKIT_API_GATEWAY_PASSWORD"]

DB_HOST = os.environ["DB_HOST"]
DB_PORT = os.environ["DB_PORT"]
DB_PASSWORD = os.environ["DB_PASSWORD"]
DB_USER = os.environ["DB_USER"]

PROJECT_NAME = "skit-pipelines"
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
INTENT_X = "intent_x"
INTENT_Y = "intent_y"
STATE = "state"

START_TOKEN = "<s>"
END_TOKEN = "</s>"
TRANSCRIPT = "transcript"

MULTI_USER = "multi_user"
KFP_RUN_FN = "create_run_from_pipeline_func"

FETCH_CALLS_NAME = "fetch-calls"
DEFAULT_FETCH_CALLS_API_RUN = "default-fetch-calls-run"

TAG_CALLS_NAME = "tag-calls"
DEFAULT_TAG_CALLS_API_RUN = "default-tag-calls-run"


KF_USERNAME = os.environ["KF_USERNAME"]
KF_PASSWORD = os.environ["KF_PASSWORD"]

USERNAME_ELEMENT_ID = 'signInFormUsername'
PASSWORD_ELEMENT_ID = 'signInFormPassword'
SUBMIT_BUTTON_ID = 'signInSubmitButton'

USERNAME_XPATH = f"(//input[@id='{USERNAME_ELEMENT_ID}'])[2]"
PASSWORD_XPATH = f"(//input[@id='{PASSWORD_ELEMENT_ID}'])[2]"
SUBMIT_XPATH = f"(//input[@name='{SUBMIT_BUTTON_ID}'])[2]"

NAME = "name"
VALUE = "value"
DOMAIN = "domain"
COOKIES_PATH = "/tmp/kf_cookies.json"
KUBEFLOW_GATEWAY_ENDPOINT = os.environ["KUBEFLOW_GATEWAY_ENDPOINT"]
COOKIE_0="AWSELBAuthSessionCookie-0"
COOKIE_1="AWSELBAuthSessionCookie-1"
COOKIE_DICT = {
    COOKIE_0: None,
    COOKIE_1: None
}
PIPELINE_HOST_URL = f"https://{KUBEFLOW_GATEWAY_ENDPOINT}/pipeline"

def CONSTRUCT_COOKIE_TOKEN(cookie_dict):
    return f"{COOKIE_0}={cookie_dict.get(COOKIE_0)};{COOKIE_1}={cookie_dict.get(COOKIE_1)}"

def GET_RUN_URL(namespace, id):
    return f"{PIPELINE_HOST_URL}/?ns={namespace}#/runs/details/{id}"

KAFKA_TOPIC_MAP = {
 FETCH_CALLS_NAME: "data-pipeline",
 TAG_CALLS_NAME: "data-pipeline"  
}