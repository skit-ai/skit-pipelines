FROM 536612919621.dkr.ecr.ap-south-1.amazonaws.com/vernacular-voice-services/ai/kubeflow/base-py:master

WORKDIR /home/kfp

RUN apt-get update \
    && apt-get install -y wget gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
RUN poetry config virtualenvs.create false

COPY ./pyproject.toml ./pyproject.toml
COPY ./poetry.lock ./poetry.lock
RUN poetry install

RUN --mount=type=secret,id=DB_HOST \
    --mount=type=secret,id=DB_PORT \
    --mount=type=secret,id=DB_PASSWORD \
    --mount=type=secret,id=DB_NAME \
    --mount=type=secret,id=DB_USER \
    --mount=type=secret,id=RANDOM_CALL_DATA_QUERY \
    --mount=type=secret,id=RANDOM_CALL_ID_QUERY \
    --mount=type=secret,id=CDN_RECORDINGS_BASE_PATH \
    --mount=type=secret,id=BUCKET \
    --mount=type=secret,id=DATA_UPLOAD_PATH \
    export DB_HOST=$(cat /run/secrets/DB_HOST) && \
    export DB_PORT=$(cat /run/secrets/DB_PORT) && \
    export DB_PASSWORD=$(cat /run/secrets/DB_PASSWORD) && \
    export DB_NAME=$(cat /run/secrets/DB_NAME) && \
    export DB_USER=$(cat /run/secrets/DB_USER) && \
    export RANDOM_CALL_DATA_QUERY=$(cat /run/secrets/RANDOM_CALL_DATA_QUERY) && \
    export RANDOM_CALL_ID_QUERY=$(cat /run/secrets/RANDOM_CALL_ID_QUERY) && \
    export CDN_RECORDINGS_BASE_PATH=$(cat /run/secrets/CDN_RECORDINGS_BASE_PATH) && \
    export BUCKET=$(cat /run/secrets/BUCKET) && \
    export DATA_UPLOAD_PATH=$(cat /run/secrets/DATA_UPLOAD_PATH)

ARG BASE_IMAGE

ENV BASE_IMAGE=$BASE_IMAGE

CMD ["/bin/sh", "-ec", "while :; do echo '.'; sleep 5 ; done"]
