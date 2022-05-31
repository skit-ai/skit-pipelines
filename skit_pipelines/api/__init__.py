from fastapi import BackgroundTasks, FastAPI
from fastapi.concurrency import run_in_threadpool
from slack_bolt import App
from slack_bolt.adapter.fastapi import SlackRequestHandler

from skit_pipelines import constants as const
from skit_pipelines.api import models

slack_app = App(token=const.SLACK_TOKEN, signing_secret=const.SLACK_SIGNING_SECRET)
app = FastAPI()
slack_handler = SlackRequestHandler(slack_app)
