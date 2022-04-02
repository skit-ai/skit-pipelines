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
