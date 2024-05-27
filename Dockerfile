FROM gpuci/miniconda-cuda:10.2-runtime-ubuntu18.04

RUN apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/3bf863cc.pub \
    && apt-get -y update \
    && apt-get install -y wget gcc libpq-dev

RUN conda install python=3.8 -y\ 
    && conda install pip\
    && conda init bash

WORKDIR /home/kfp

RUN apt-get update && apt-get install -y --fix-missing \
    libxss1 libappindicator1 libindicator7 jq \
    && rm -rf /var/lib/apt/lists/*

# Install latest Chrome
RUN LATEST_CHROME_RELEASE=$(curl -s https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json | jq '.channels.Stable') \
    && echo "LATEST_CHROME_RELEASE: $LATEST_CHROME_RELEASE" \
    && LATEST_CHROME_URL=$(echo "$LATEST_CHROME_RELEASE" | jq -r '.downloads.chrome[] | select(.platform == "linux64") | .url') \
    && echo "LATEST_CHROME_URL: $LATEST_CHROME_URL" \
    && wget -N "$LATEST_CHROME_URL" -P /root/ \
    && unzip /root/chrome-linux64.zip -d /root/ \
    && mv /root/chrome-linux64 /root/chrome \
    && ln -s /root/chrome/chrome /usr/local/bin/chrome \
    && chmod +x /usr/local/bin/chrome \
    && rm /root/chrome-linux64.zip

# Install Chromedriver
RUN LATEST_CHROME_RELEASE=$(curl -s https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json | jq '.channels.Stable') \
    && LATEST_CHROME_DRIVER_URL=$(echo "$LATEST_CHROME_RELEASE" | jq -r '.downloads.chromedriver[] | select(.platform == "linux64") | .url') \
    && echo "LATEST_CHROME_DRIVER_URL: $LATEST_CHROME_DRIVER_URL" \
    && wget -N "$LATEST_CHROME_DRIVER_URL" -P /root/ \
    && unzip /root/chromedriver-linux64.zip -d /root/ \
    && mv /root/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver \
    && chmod +x /usr/local/bin/chromedriver \
    && rm /root/chromedriver-linux64.zip

# set display port to avoid crashgit
ENV DISPLAY=:99

RUN apt-get -y update\
    && apt-get -y --fix-missing install libblas-dev liblapack-dev gfortran ffmpeg cmake

# install johnny.
RUN curl -s https://api.github.com/repos/skit-ai/johnny/releases/latest \
    | grep "\"browser_download_url.*linux-amd64.tar.gz\"" \
    | cut -d : -f 2,3 | tr -d \" \
    | wget -qi - -O johnny.tar.gz \
    && tar -xvzf johnny.tar.gz \
    && pwd \
    && ls -lat .

RUN conda install git pip
RUN pip install git+https://github.com/skit-ai/eevee.git@1.3.0
RUN pip install -U pip setuptools && pip install poetry==1.2.2 numpy==1.22.0 regex==2022.7.25 pygit2==1.10.0
RUN poetry config virtualenvs.create false

RUN conda install scipy

COPY . .

RUN poetry install --only main && poetry install --only main


ARG BASE_IMAGE
ARG CUDA_IMAGE
ARG ECR_REGISTRY
ARG REGION

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

ARG PERSONAL_ACCESS_TOKEN_GITHUB
ARG PERSONAL_ACCESS_TOKEN_GITLAB

ARG DUCKLING_HOST

ARG GOOGLE_SHEETS_CREDENTIALS

ARG CDN_RECORDINGS_BASE_PATH
ARG BUCKET

ARG S3_US_PRODUCTION_TURN_RECORDINGS_BUCKET

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
ARG JWT_SECRET_KEY
ARG KAFKA_INSTANCE

ARG OPENAI_API_KEY
ARG OPENAI_COMPLIANCE_BREACHES_KEY

ARG AWS_ACCESS_KEY_ID
ARG AWS_SECRET_ACCESS_KEY

ENV ECR_REGISTRY=$ECR_REGISTRY
ENV REGION=$REGION
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

ENV PERSONAL_ACCESS_TOKEN_GITHUB=$PERSONAL_ACCESS_TOKEN_GITHUB
ENV PERSONAL_ACCESS_TOKEN_GITLAB=$PERSONAL_ACCESS_TOKEN_GITLAB

ENV DUCKLING_HOST=${DUCKLING_HOST}

ENV RANDOM_CALL_DATA_QUERY=secrets/random_calls_data.sql
ENV RANDOM_CALL_ID_QUERY=secrets/random_call_ids.sql
ENV CALL_IDS_FROM_UUIDS_QUERY=secrets/call_ids_from_uuids.sql
ENV LABELSTUDIO_TOKEN=$LABELSTUDIO_TOKEN

ENV GOOGLE_SHEETS_CREDENTIALS=$GOOGLE_SHEETS_CREDENTIALS

ENV CDN_RECORDINGS_BASE_PATH=$CDN_RECORDINGS_BASE_PATH
ENV BUCKET=$BUCKET

ENV S3_US_PRODUCTION_TURN_RECORDINGS_BUCKET=$S3_US_PRODUCTION_TURN_RECORDINGS_BUCKET

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
ENV JWT_SECRET_KEY=$JWT_SECRET_KEY

ENV KAFKA_INSTANCE=$KAFKA_INSTANCE
ENV OPENAI_API_KEY=$OPENAI_API_KEY
ENV OPENAI_COMPLIANCE_BREACHES_KEY=$OPENAI_COMPLIANCE_BREACHES_KEY
ENV AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID
ENV AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY

CMD ["/bin/sh", "-ec", "while :; do echo '.'; sleep 5 ; done"]
