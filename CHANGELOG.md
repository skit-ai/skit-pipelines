# Changelog
## 0.2.44
- [x] update: gitlab token secret

## 0.2.43
- [x] update: `retrain_slu` pipeline changes to align with new Deployment CI/CD for SLU (#76)
- [x] add: raise exception when no calls found/csv empty (#75)

## 0.2.42
- [x] update: skit-labels version bump 0.3.29
- [x] update: discrepancy check for raw.intent and intent column for test dataset in retrain_slu_from_repo component

## 0.2.40
- [x] update: force utterances as str in gen_asr_metrics component (#71)
- [x] add: checks for 0 byte audios before uploading for tagging (#72)
- [x] add: custom port support while testing pipeline
- [x] update: Extending `retrain_slu` pipeline features (#73)
- [x] fix: entity pipelines supporting labelstudio datasets (#74)

## 0.2.39
- [x] update: Asr tune pipeline enhancements (#70

## 0.2.38
- [x] update: secrets + us ml metrics db env vars
- [x] update: upload2s3 upload directories, asr_tune uploads directory and process true transcript in asr_eval_pipeline (#69)

## 0.2.37
- [x] fix: preprocess step skipped for lablestudio (#68)

## 0.2.36
- [x] update: irr fixes for labelstudio datasets (#66)

## 0.2.35
- [x] add: slack bots and channels based on cluster region

## 0.2.34
- [x] fix: again pipeline_constants not defined error in asr_tune component (#65)

## 0.2.32
- [x] fix: regionwise nodeselector for pipelines

## 0.2.31
- [x] fix: pipeline_constants not defined error in asr_tune component (#63)
## 0.2.30
- [x] fix: empty_possible param for download_file_from_s3 component

## 0.2.29
- [x] fix: involving nan + adjusting for interval types - `fetch_tagged_entity_dataset` pipeline
- [x] add: lm tuning pipeline (#58)
- [x] update: `download_from_s3` component into downstream components
- [x] add: auto nodeselector based on pipeline type - cpu/gpu (#60)
- [x] update: fetch data from multiple job/project ids at once (combined data) (#61)
- [x] add: Transcription Pipeline V1 (#56)
- [x] add: `retrain_slu` pipeline for automated SLU retraining with deployment tracked using gitlab. (#62)

## 0.2.28
- [x] fix: if not project_id present then only force routes for selected clients - tag_calls.

## 0.2.27
- [x] fix: org_id type being different across components.

## 0.2.26
- [x] add: eer pipelines (#55)

## 0.2.25
- [x] add: fetch_tagged_entity_dataset pipeline. (#54)

## 0.2.24
- [x] update: force route tagging requests to labelstudio. (#53)

## 0.2.23
- [x] add: offset for pulling last n days fetch_tagged_dataset op, and thus used in irr_from_tog pipeline (#49)

## 0.2.22

- [x] add: Authentication and Authorization of requests using JWT - Oauth2

## 0.2.21

- [x] update: eevee yaml component for exhaustive possible intent metrics

## 0.2.19

- [x] update: version bump for skit-calls and skit-labels
- [x] update: new `AUDIO_URL_DOMAIN` secret for param in fetch_calls component

## 0.2.18

- [x] fix: bugs in eval_asr_pipeline

## 0.2.17

- [x] fix: slackbot command parser for base64 breaking when period (.) at end of text
- [x] add: run pipelines from func, without uploading yamls + easier dev workflow
- [x] add: asr-eval-pipeline phase 1
- [x] update: `irr_from_tog` now has `mlwr=True` arg (which also requires `slu_project_name`) for pushing calculated eevee metrics on a tog job to ml-metrics db, intent_metrics table


## 0.2.16

- [x] update: start_date and end_date optional for fetch_calls_pipeline, fetch_n_tag_calls, fetch_calls_n_push_to_sheets and fetch_calls_n_upload_tog_and_sheet

## 0.2.15

- [x] update: `skit-labels` version bump to 0.3.27 - tag_calls and fetch_n_tag_calls uploads data in batches of batched data with retries + sleep.

## 0.2.14

- [x] fix: call_type default arg from "inbound" to "INBOUND" for fetch_calls_pipeline
- [x] fix: eval_voicebot_xlmr_pipeline to work even when model is not present

## 0.2.13

- [x] update: `skit-labels` version bump to 0.3.26

## 0.2.12

- [x] add: `irr_from_tog` pipeline, it takes a tog job id/ labelstudio project id and outputs eevee's intent metrics uploaded to s3 & optionally posted on slack, an addition to eval_voicebot_xlmr_pipeline.

## 0.2.7

- [x] update: skit-calls version bump to 0.2.21

## 0.2.6

- [x] add: use slackbot reminders to run/schedule recurring pipelines
- [x] update: skit-calls version bump to 0.2.19

## 0.2.5

- [x] update: date time offsets for data pipelines.
- [x] update: tarfile uploads for directories.

## 0.2.4

- [x] fix: uploading dirs to s3
- [x] fix: tagging response defined before use.

## 0.2.3

- [x] update: xlmr eval output as csv.

## 0.2.2

- [x] fix: evaluation pipeline for intent evaluation on f1-score metric.

## 0.2.1

- [x] fix: training pipeline accomodates older/newer datasets.
- [x] update: tag calls raises exception if neither of tog/labelstudio ids are provided.
- [x] update: tag calls raises exception if no data was uploaded.

## 0.2.0

- [x] fix: slack parser handles urls in code blocks.
- [x] update: add slack thread id, channel and user id automatically.
- [x] update: slack notification component expects code_blocks instead of s3_path.
- [x] fix: slack parser compatible with python 3.8
- [x] fix: notfications are sent to slack threads if thread id is present.
- [x] feat: Notify users when a pipeline run is complete / failed.
- [x] update: tag calls returns multiple outputs.

## 0.1.99

- [x] fix: auth-token type.

## 0.1.98

- [x] fix: training pre-proc handles utterances from these columns as well: alternatives, data.

## 0.1.97

- [x] update: dockerfile uses python 3.8 and cuda 10.2.
- [x] fix: labelstudio download.
- [x] update: compatible with python 3.8.

## 0.1.96

- [x] update: normalize.comma_sep_str can be used for comma separated numbers and strings.

## 0.1.95

- [x] fix: TypeError: Object of type JSONDecodeError is not JSON serializable on dataset uploads.
- [x] fix: invalid literal for int() with base 10: '' on dataset uploads

## 0.1.94

- [x] update: skit-labels unpacks tagged dataset.
- [x] fix: 'AttributeError: 'NoneType' object has no attribute 'get' on fetching calls with failed predictions.
- [x] fix: compatibility between skit-labels, skit-calls, skit-auth, kfp, etc.
- [x] add: s3 url support for tag calls pipeline.

## 0.1.93

- [x] fix: Slack hyperlink markup removed.

## 0.1.92

- [x] add: Labelstudio integration.

## 0.1.91

- [x] update: fetch_calls_n_upload_tog_and_sheet and fetch_calls_n_push_to_sheets pipelines refactor

## 0.1.90

- [x] update: replace org-id with reference in s3 upload component.

## 0.1.89

- [x] fix: storage options.

## 0.1.88

- [x] fix: slack token const.
- [x] refactor: unused types.

## 0.1.87

- [x] fix: db host name.
- [x] update: default arguments fixed.

## 0.1.86

- [x] docs: Better examples, easier to copy paste commands.
- [x] add: slack notifications to all components.

## 0.1.85

- [x] fix: slack urls.
- [x] add: slack notifications to all components.

## 0.1.84

- [x] add: slack signing secret.

## 0.1.83

- [x] docs: Pipeline and payload docs added.
- [x] update: slackbot command parser responds with stacktrace.

## 0.1.82

- [x] fix: No module named 'skit_pipelines' caused by installing before copy source in dockerfile.
- [x] refactor: makefile for building pipelines is leaner.

## 0.1.80

- [x] add: slack-bot integration. Invoke pipelines via slackbot.
- [x] refactor: Automatic generation of pydantic models using kfp signature.

## 0.1.79

- [x] add: intent evaluation pipeline.
- [x] add: crr evaluation pipeline.
- [x] add: slack-bot integration.

## 0.1.62
- [x] update: remove helper function for upload2sheet
- [x] update: sheet duplication and row logic while pushing calls to google sheet

## 0.1.53
- [x] update: move helper functions of upload2sheet into a folder

## 0.1.52
- [x] update: skit-calls==0.2.15

## 0.1.48
- [x] update: skit-calls==0.2.14

## 0.1.45
- [x] fix: to make Docker file and github actions yaml to use google secrets

## 0.1.44
- [x] update: component to push CSV to a google sheet. Load google secrets from a Github secrets
- [x] update: Docker file and github actions yaml to use google secrets
## 0.1.43
- [x] add: component to push CSV to a google sheet.
- [x] add: pipeline to fetch calls and push to google sheet.

## 0.1.42

- [x] update: XLMR training supports lr parameter.

## 0.1.41

- [x] update: skit-calls==0.2.13

## 0.1.40

- [x] update: skit-labels==0.3.21
- [x] update: ping users on slack channels.

## 0.1.39

- [x] update: skit-calls==0.2.12
- [x] update: remove recurrent from fetch-n-tag pipeline and start_date, end_date logic moved to skit-calls instead.

## 0.1.38

- [x] update: skit-calls==0.2.11
- [x] update: skit-labels==0.3.20
- [x] fix: save labelencoder pickle while running the train xlmr pipeline.

## 0.1.32

- [x] update: remove dvc link for pipelines.
- [x] add: makefile downloads secrets from skit-calls.

## 0.1.26

- [x] feat: APIs for pipelines.
- [x] add: secrets via dvc.

## 0.1.25

- [x] add: pipeline to fetch and tag a dataset.
- [x] fix: support legacy dataframes missing utterance columns.

## 0.1.24

- [x] update: XLMR intent classifier training pipeline pushes models to s3.

## 0.1.23

- [x] update: trained models upload to s3.

## 0.1.22

- [x] add: Conda and Cuda within base docker image.

## 0.1.21

- [x] add: Cuda installation within Dockerfile.
- [x] fix: Intent classifier training component.

## 0.1.20

- [x] fix: intent classifier featurizer fixed to apply row-wise transformation.
- [x] fix: hacky solution for https://github.com/ThilinaRajapakse/simpletransformers/issues/1386

## 0.1.19

- [x] update: kfp installed within container.

## 0.1.18

- [x] update: components isolated from helper functions.

## 0.1.17

- [x] add: component to create utterance column `utterances`.
- [x] add: component to create true intent column `intent_y`.
- [x] add: component to add state and utterances as features for intent classifer (xlmr).
- [x] update: model training pipeline with train set only.

## 0.1.16

- [x] add: torch = "^1.11.0" for cuda 10.2

## 0.1.15

- [x] add: preprocessing module for specialized components.

## 0.1.14

- [x] update: skit-labels 0.3.17 with higher tolerance for utterance structures.

## 0.1.13

- [x] update: skit-labels skit-calls for serialized json fields.

## 0.1.12

- [x] update: skit-labels 0.3.13, values for db creds resolved.

## 0.1.11

- [x] add: placeholder component to train xlmr intent classifier.

## 0.1.10

- [x] add: component that fetches tagged datasets.
- [x] add: kubeflow pipeline utilizing the above component.

## 0.1.9

- [x] update: skit-calls 0.2.3

## 0.1.8

- [x] fix: Slack notification component -- Slack token constant.

## 0.1.7

- [x] fix: Slack notification component -- Slack token constant.

## 0.1.6

- [x] update: link slack component with fetch data pipeline.

## 0.1.5

- [x] feat: slack integration.

## 0.1.4

- [x] update: skit-pipelines is available within docker image.

## 0.1.3

- [x] update: build pipeline yamls via `make`.

## 0.1.2

- [x] refactor: modularize project.

## 0.1.1

- [x] add: boto3 for s3 upload/download.

## 0.1.0

- [x] add: calls dataset component.
- [x] add: Upload to s3 component.
- [x] add: Calls dataset pipeline.
- [x] add: workflow to automate docker image creation on tag push.
