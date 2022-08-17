FROM gpuci/miniconda-cuda:10.2-runtime-ubuntu18.04

RUN apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/3bf863cc.pub \
    && apt-get -y update \
    && apt-get install -y wget gcc libpq-dev

RUN conda install python=3.8 -y\ 
    && conda install pip\
    && conda init bash

WORKDIR /home/kfp

RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
RUN apt-get -y update\
    && apt-get -y install google-chrome-stable

# install chromedriver
RUN apt-get install -yqq unzip
RUN wget -O /tmp/chromedriver.zip http://chromedriver.storage.googleapis.com/`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE`/chromedriver_linux64.zip
RUN unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/\
    && rm /tmp/chromedriver.zip\
    rm -rf /var/lib/apt/lists/*

# set display port to avoid crashgit
ENV DISPLAY=:99

RUN apt-get -y update\
    && apt-get -y install libblas-dev liblapack-dev gfortran

RUN conda install git pip
RUN pip install git+https://github.com/skit-ai/eevee.git@1.3.0
RUN pip install poetry==1.1.14 regex==2022.7.25 pygit2==1.10.0
RUN poetry config virtualenvs.create false

RUN conda install scipy

COPY pyproject.toml .

RUN poetry install --no-dev

COPY . .

RUN poetry install --no-dev

ARG BASE_IMAGE
ARG CUDA_IMAGE

ARG DB_HOST
ARG DB_PORT
ARG DB_NAME
ARG DB_PASSWORD
ARG DB_USER

ARG ML_METRICS_DB_HOST
ARG ML_METRICS_DB_PORT
ARG ML_METRICS_DB_NAME
ARG ML_METRICS_DB_USER
ARG ML_METRICS_DB_PASSWORD

ARG GITHUB_PERSONAL_ACCESS_TOKEN

ARG GOOGLE_SHEETS_CREDENTIALS

ARG CDN_RECORDINGS_BASE_PATH
ARG BUCKET

ARG SLACK_TOKEN
ARG SLACK_SIGNING_SECRET
ARG DEFAULT_SLACK_CHANNEL

ARG AUDIO_URL_DOMAIN
ARG SKIT_API_GATEWAY_URL
ARG SKIT_API_GATEWAY_EMAIL
ARG SKIT_API_GATEWAY_PASSWORD
ARG TOG_TASK_URL
ARG LABELSTUDIO_TOKEN

ARG KUBEFLOW_GATEWAY_ENDPOINT
ARG KF_USERNAME
ARG KF_PASSWORD
ARG KAFKA_INSTANCE

ENV BASE_IMAGE=$BASE_IMAGE
ENV CUDA_IMAGE=$CUDA_IMAGE

ENV DB_HOST=$DB_HOST
ENV DB_PORT=$DB_PORT
ENV DB_PASSWORD=$DB_PASSWORD
ENV DB_NAME=$DB_NAME
ENV DB_USER=$DB_USER

ENV ML_METRICS_DB_NAME=$ML_METRICS_DB_NAME
ENV ML_METRICS_DB_HOST=$ML_METRICS_DB_HOST
ENV ML_METRICS_DB_PORT=$ML_METRICS_DB_PORT
ENV ML_METRICS_DB_USER=$ML_METRICS_DB_USER
ENV ML_METRICS_DB_PASSWORD=$ML_METRICS_DB_PASSWORD

ENV GITHUB_PERSONAL_ACCESS_TOKEN=$GITHUB_PERSONAL_ACCESS_TOKEN

ENV RANDOM_CALL_DATA_QUERY=secrets/random_calls_data.sql
ENV RANDOM_CALL_ID_QUERY=secrets/random_call_ids.sql
ENV CALL_IDS_FROM_UUIDS_QUERY=secrets/call_ids_from_uuids.sql
ENV LABELSTUDIO_TOKEN=$LABELSTUDIO_TOKEN

ENV GOOGLE_SHEETS_CREDENTIALS=$GOOGLE_SHEETS_CREDENTIALS

ENV CDN_RECORDINGS_BASE_PATH=$CDN_RECORDINGS_BASE_PATH
ENV BUCKET=$BUCKET

ENV SLACK_TOKEN=$SLACK_TOKEN
ENV SLACK_SIGNING_SECRET=$SLACK_SIGNING_SECRET
ENV DEFAULT_SLACK_CHANNEL=$DEFAULT_SLACK_CHANNEL

ENV AUDIO_URL_DOMAIN=$AUDIO_URL_DOMAIN
ENV SKIT_API_GATEWAY_URL=$SKIT_API_GATEWAY_URL
ENV SKIT_API_GATEWAY_EMAIL=$SKIT_API_GATEWAY_EMAIL
ENV SKIT_API_GATEWAY_PASSWORD=$SKIT_API_GATEWAY_PASSWORD
ENV TOG_TASK_URL=$TOG_TASK_URL

ENV KUBEFLOW_GATEWAY_ENDPOINT=$KUBEFLOW_GATEWAY_ENDPOINT
ENV KF_USERNAME=$KF_USERNAME
ENV KF_PASSWORD=$KF_PASSWORD

ENV KAFKA_INSTANCE=$KAFKA_INSTANCE

CMD ["/bin/sh", "-ec", "while :; do echo '.'; sleep 5 ; done"]
