# Changelog
1.2.5
- [x] fix: Missing dependency in chrome installation

1.2.4
- [x] fix: Upgrade Selenium version

1.2.3
- [x] fix: Chrome and chromedriver issue for image build

1.2.2
- [x] update: Update Gitlab personal token

1.2.1
- [x] remove: Remove support for fetch_n_tag_calls and tag_calls

1.1.24
- [x] add: Support for a new column in conversations table

1.1.23
- [x] Bugfix: Fix missing metrics folder and s3 upload region

1.1.22
- [x] add: blocking_disposition is now being extracted as part of call-level tagging jobs

1.1.21
- [x] add: Pipeline to invalidate situations in DB for LLMs

1.1.20
- [x] add: New s3_buckets for sandbox regions in India and US

1.1.19
- [x] add: previous_disposition is now being extracted as part of call-level tagging jobs

1.1.18
- [x] Bugfix: fix issue with sample conversation display

1.1.17
- [x] Update skit-labels version

1.1.16
- [x] Bugfix: Fix db connection issue

1.1.15
- [x] add: Pipeline to generate conversations and upload it for tagging

1.1.14
- [x] Update github access token in secrets

1.1.12
- [x] Bugfix: fix issue with fetch_calls pipeline

1.1.11
- [x] Bugfix: fix issue with retrain_slu_old pipeline

1.1.10
- [x] Bugfix: update skit-calls version

1.1.9
- [x] add: Change node selector in US

1.1.8
- [x] add: support for displaying a sample of the conversation generated

1.1.7
- [x] fix: the handling of the format of scenario param in generate sample conversations pipeline

1.1.6
- [x] add: Pipeline for generating sample conversations

1.1.5
- [x] fix: No calls found from FSM shouldnt fail data_fetch pipelines

1.1.4
- [x] fix: Intent list was not coming in comprision file while training or evaluate slu.

1.1.3
- [x] Update node selector to match node groups in US

1.1.2
- [x] add environment variables in CI

1.1.1
- [x] add: Added re_presign_s3_urls component, which can re-presign publis s3 http urls in transcription_pipeline.
- [x] fix: join on dataframes bug fix at merge_transcription component.


1.1.0
- [x] add: Added evaluate_slu pipeline in the repo to test the slu
- [x] add: Added features of comparing repo while testing
- [x] fix: created multiple component to reduce the retendency and complaxity of repo.
- [x] fix: Moved common funtions in seperate utils files for retrain and evaluate slu.

1.0.7
- [x] Update credentials for accessing fsm DB
- [x] Add support for multiple flow ids for fetch call related pipelines

1.0.6
- [x] Bugfix: update skit-calls version

1.0.4
- [x] Bugfix: Dvc config updated only for new SKU repos

1.0.2
- [x] Add support for obtaining comparision confusion matrix while retraining SLU

1.0.0
- [x] Remove deprecated pipelines

0.2.105
- [x] Functionality to compare new trained SLU model with live model on test data (#115)

0.2.104
- [x] Fixes issue with chrome browser and driver mismatch (#116)

0.2.103
- [x] Add retry for LS uploads in skit-labels (#22)

0.2.102
- [x] Redact user info using presidio (#113)
- [x] updated aws creds

0.2.101
- [x] add: s3 client aws access id and keys secrets

0.2.99
- [x] alias_bug_fix: fixes issue in dowloading yaml file. (#112)
- [x] Update key related dependencies and add time logger (#110)

0.2.98
- [x] Add new pipeline to identify and persist ML compliance breaches in calls

0.2.97
- [x] fix: logs streaming during train and test (#108)

0.2.96
- [x] add: skit-calls version bump for presigned-url logic for turn audio url in US cluster

0.2.95
- [x] Refactor retraining pipelines for new SLU architecture (#107)

0.2.94
- [x] download_yaml: chnages in alias file download from gitlab repo. (#106), storage_full_fix: Removig old_data while velidating pipelines.

0.2.92
- [x] fix: template_id not working properly, changed skit-calls query secrets
- [x] PL-1300: new data format support & extra meta-annotation-columns (#21)

0.2.91
- [x] Extend GPT support for fetch_n_tag_calls and update prompts (#104)
- [x] transcription pipeline: add support for mp3 file format while overlaying transcriptions (#103) 

0.2.90
- [x] update: Secrets for assisted annotation pipeline

0.2.89
- [x] add: Slu customization integration with retrain_slu pipeline (#102)
- [x] add: support for call level tagging jobs for tag_calls pipeline, alongwith turn level tagging

0.2.88
- [x] add: Merge pull request #99 from skit-ai/gpt_intents

0.2.87
- [x] add: validate setup component for retrain_slu pipeline, tests slu setup builds in cpu node

0.2.86
- [x] update: skit-calls and skit-labels version update
- [x] fix: alternatives column postprocessing after downloading from labelstudio, client_id not being truly optional for fetch_calls component  

0.2.84
- [x] update: skit-calls version bump for reftime with timezone

0.2.83
- [x] update: skit-calls version bump and use_fsm_url as param for all fetch_calls related pipelines

0.2.82
- [x] add: comma separated list of client_id is supported, template_id to filter calls is supported. Both in fetch_calls component + also modified downstream pipelines using it

0.2.81
- [x] fix: upstream column names for entity tagged dataset
- [x] update: version bump for skit-calls which helps to sample turns in a call based on comma separated list of intents

0.2.80
- [x] [PL-997] adding more call metadata from upstream for CRR tagging

0.2.79
- [x] add: skit-calls version bump which includes new columns for fetch_calls component returned csv - call_type, disposition, call_end_status, flow_name

0.2.78
- [x] update: buffer for call_quantity for fetch_calls component

0.2.77
- [x] update: use_fsm_url flag based on region for deciding turn audio uri paths should be from fsm or s3 bucket directly
- [x] update: skit-calls version bump for use-fsm-url flag
- [x] update: org_auth_token component's output is optional since tog deprecated

0.2.76
- [x] fix: made console URL region specific to fix call & slot tagging job uploads (esp in US)

0.2.75
- [x] update: removed audio validation from fetch_calls component as min_duration is present now.

0.2.74
- [x] add: get pipeline run error logs as slackbot message (#93)

0.2.73
- [x] update: skit-calls version bump - calls-with-cors path removal for audio_url in fetched calls.

0.2.72
- [x] fix: granular time filters not getting applied for ml fetch calls pipelines - date offset


0.2.71
- [x] fix: granular time filters not getting applied for ml fetch calls pipelines

## 0.2.70
- [x] skit-calls version bump for minute offset to def process_date_filters - in fetch_calls component

## 0.2.69
- [x] revert: "cache the poetry install step for faster docker builds and dev experience (#90)" (#92)

## 0.2.68
- [x] update: skit-calls version bump to 0.2.27 for sampling call on min_duration

## 0.2.67
- [x] fix: Auto-MR creation breaks in SLU training pipeline when classification report / confusion matrix is long (#91)
- [x] update: use poetry version only what mentioned in SLU repo in retrain_slu pipeline
- [x] update: cache the poetry install step for faster docker builds and dev experience (#90)
- [x] fix: asr tune pull request #89 from skit-ai/asr_tune_hi_fix


## 0.2.66
- [x] update: upload same data to multiple labelstudio project ids

## 0.2.65
- [x] add: new component file_contents_to_markdown for better gitlab mr description with reports (#88)

## 0.2.64
- [x] fix: `data_label` bug

## 0.2.63
- [x] update: set default value of `data_label` as `Live`

## 0.2.62
- [x] fix: `remove_empty_audios` not setting to false for fetch_calls

## 0.2.61
- [x] add: `remove_empty_audios` param controllable for fetch_calls_pipeline

## 0.2.60
- [x] update: make docs

## 0.2.59
- [x] update: remove default option for data_label in all tag_call component involving pipelines

## 0.2.58
- [x] add: mandatory data_label field for tag_calls component
- [x] add: optional data_labels field for fetch_tagged_data_from_labelstore component
- [x] update: skit-labels version bump to 0.3.31

## 0.2.57
- [x] fix: skit-calls secrets query for language - version bump to 0.2.26

## 0.2.56
- [x] update: skit-calls version bump to 0.2.25
- [x] fix: upload2s3 folder upload bug

## 0.2.55
- [x] upload2s3: correct bug in upload_as_directory that leads to flattening of path_on_disk contents in the target output_path (#82)
- [x] change: changed the parser for Hindi from Unified Parser to Character split. This is a breaking change and support for ASR models hi-v4 and b
elow is removed (#83)

## 0.2.54
- [x] add: new pipeline for pushing same data for intent, entities & slot/call tagging (#81)

## 0.2.53
- [x] fix: retrain slu pipeline fails when only s3 uri provided

## 0.2.52
- [x] update: label store data format and query changes (#80)

## 0.2.51
- [x] update: db_host const
- [x] add: timezone based on cluster region

## 0.2.50
- [x] add: fetch_tagged_data_from_labelstore pipeline (#79)
- [x] fix: intent column placeholder for slu train pipeline

## 0.2.49
- [x] fix: upstream changes made by fetch_tagged_dataset component (#78)

## 0.2.48
- [x] update: single function handling both tog and labelstudio data fetching - skit-labels version bump
- [x] update: skit-calls version bump to 0.2.24

## 0.2.47
- [x] fix: call_type bug for inbound/outbound only
- [x] fix: downgrade google-auth-oauthlib to 0.4.6 (#77)

## 0.2.46
- [x] update: for pipeines using `fetch_calls` component, call_type defaults to "inbound" and "outbound" both
- [x] update: skit-calls version bump to 0.2.23 

## 0.2.45
- [x] fix: training pipeline bug
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
