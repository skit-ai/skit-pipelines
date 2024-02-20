.. skit_pipelines documentation master file, created by
   sphinx-quickstart on Mon Sep  4 15:11:40 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Skit-pipelines
==============

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: Pipelines

   Random sample calls <./skit_pipelines.pipelines.fetch_calls_pipeline>
   Random sample and tag calls <./skit_pipelines.pipelines.fetch_n_tag_calls>
   Download tagged dataset <./skit_pipelines.pipelines.fetch_tagged_calls_dataset>
   Upload for annotation <./skit_pipelines.pipelines.tag_calls>
   Download tagged entity dataset <./skit_pipelines.pipelines.fetch_tagged_entity_dataset>
   Retrain SLU <./skit_pipelines.pipelines.retrain_slu>
   Publish Complaince Breaches <./skit_pipelines.pipelines.publish_compliance_breaches>
   Transcribe Dataset <./skit_pipelines.pipelines.transcription_pipeline>
   Random sample and tag turns and calls <./skit_pipelines.pipelines.fetch_n_tag_turns_and_calls>
   Generate sample conversations for LLMs <./skit_pipelines.pipelines.generate_sample_conversations>
   Generate conversations for LLMS and upload it for tagging <./skit_pipelines.pipelines.generate_and_tag_conversations>


Reusable workflows for ml teams at skit.ai. Built using `kubeflow components <https://pypi.org/project/kfp/>`_. 

[`Contribution guide <https://github.com/skit-ai/skit-pipelines/blob/main/CONTRIBUTING.md>`_]

Components
----------

A component does *one thing really well*. As an example, if you want to download a dataset and train a model:

1. You would query a database.
2. Save the results as a file.
3. Prepare train/test datasets for training.
4. Run a program to train the model.
5. Save the model once training is complete.
6. Evaluate the model on the test set to benchmark performance.
7. Run 1 - 6 till results are favourable.
8. Persist the best model on the cloud.
9. Persist the best results on the cloud.

Each step here is a component. As long as components ensure single responsibility we can build complex pipelines conveniently.

.. attention::

   If a component trains a model after performing a 70-30 split on a given dataset. 
   It would be very difficult to train if we have a dataset that should be used entirely for training.
   The component will helplessly reduce 30% of the data **always**.

Pipelines
---------

Pipelines are complex ML workflows that are required regularly like: training a model, sampling data, getting data annotated, producing metrics, etc.

Here's a list of official pipelines, within these docs we share snippets for slack-bot invocations:

+--+----------------------------------------------------------------------------------+
|   | Pipelines                                                                       |
+==+==================================================================================+
| 1 | :ref:`Random sample and tag calls <p_fetch_n_tag_calls>`                        |
+--+----------------------------------------------------------------------------------+
| 2 | :ref:`Random sample calls <p_fetch_calls_pipeline>`                             |
+--+----------------------------------------------------------------------------------+
| 3 | :ref:`Download tagged dataset <p_fetch_tagged_calls_dataset>`                   |
+--+----------------------------------------------------------------------------------+
| 4 | :ref:`Upload for annotation <p_tag_calls>`                                      |
+--+----------------------------------------------------------------------------------+
| 5 | :ref:`Download tagged entity dataset <p_fetch_tagged_entity_dataset>`           |
+--+----------------------------------------------------------------------------------+
| 6 | :ref:`Publish Compliance breaches <p_publish_compliance_breaches>`              |
+--+----------------------------------------------------------------------------------+
| 7 | :ref:`Transcribe Dataset <p_transcription_pipeline>`                            |
+--+----------------------------------------------------------------------------------+
| 8 | :ref:`Retrain SLU <p_retrain_slu>`                                              |
+--+----------------------------------------------------------------------------------+
| 9 | :ref:`Random sample and tag turns and calls <p_fetch_n_tag_turns_and_calls>`    |
+--+----------------------------------------------------------------------------------+
| 10 | :ref:`Generate sample conversations <p_generate_sample_conversations>`         |
+--+----------------------------------------------------------------------------------+
| 11 | :ref:`Generate and upload conversations <p_generate_and_tag_conversations>`    |
+--+----------------------------------------------------------------------------------+
| 12 | :ref:`Invalidate situations in DB for LLMS <p_invalidate_llm_situations_in_db>` |
+--+----------------------------------------------------------------------------------+

Project strucuture
------------------

Understand the directory strucuture.

.. code-block:: shell

   .
   ├── build
   │   └── fetch_calls_pipeline.yaml
   ├── ... (skipping other files)
   ├── skit_pipelines
   │   ├── components
   │   │   ├── fetch_calls.py
   │   │   ├── __init__.py
   │   │   └── upload2s3.py
   │   ├── constants.py
   │   ├── __init__.py
   │   ├── pipelines
   │   │   ├── fetch_calls_pipeline.py
   │   │   └── __init__.py
   │   └── utils
   │       └── __init__.py
   └── tests

- We have `components` module, each file corresponds to exactly one component.
- We have `pipelines` module, each file corresponds to exactly one pipeline.
- Reusable functions should go to `utils`.
- We have `constants.py` file that contains constants to prevent typos and assist with code completion.
- `build` houses our pipeline yamls. These will get more important in a later section.

It is necessary to understand the anatomy of a kubeflow `component <https://www.kubeflow.org/docs/components/pipelines/sdk/component-development/>`_ 
and `pipeline <https://www.kubeflow.org/docs/components/pipelines/sdk/build-pipeline/>`_ before contributing to this project.


Making new pipelines
--------------------

Once a new pipeline and its pre-requisite components are ready.

1. Add an entry to the :code:`CHANGELOG.md`.
2. Create a new tag with updated semver and push, our github actions take care of pushing the image to our private ECR.
3. Run :code:`make all`. This will rebuild all the pipeline yamls. This will create a secrets dir. Doesn't work if you don't have s3 credentials.
4. Run :code:`source secrets/env.sh` You may not have this if you aren't part of skit.ai.
5. Upload the yamls to `kubeflow ui <https://www.kubeflow.org/docs/components/pipelines/sdk/build-pipeline/#option-1-compile-and-then-upload-in-ui>`_ or `use it via the sdk <https://www.kubeflow.org/docs/components/pipelines/sdk/build-pipeline/#option-2-run-the-pipeline-using-kubeflow-pipelines-sdk-client>`_.

Pre-requisites
--------------

- This project is based on :code:`python 3.10`. You would require an environment setup for the same. Using `miniconda <https://docs.conda.io/en/latest/miniconda.html>`_ is recommended.
- make `mac <https://formulae.brew.sh/formula/make>`_
- `poetry <https://python-poetry.org/docs/#installation>`_

Local development
-----------------

- Source secrets.

   .. code-block:: bash

      dvc pull && source secrets/env.sh

- Run

   .. code-block:: bash

      uvicorn skit_pipelines.api.endpoints:app \
      --proxy-headers --host 0.0.0.0 \
      --port 9991 \
      --workers 1 \
      --reload


Responses
---------

Endpoint responses
##################

   .. code-block:: json

      {
         "status":"ok",
         "response":{
            "message":"Pipeline run created successfully.",
            "name":"train-voicebot-xlmr",
            "run_id":"e33879a1-xxxxx",
            "run_url":"https://kubeflow.skit.ai/pipeline/?ns=..."
         }
      }

Webhook responses
#################

Success
^^^^^^^
.. code-block:: json

   {
      "status": "ok",
      "response": {
         "message": "Run completed successfully.",
         "run_id": "662b9909-d251-45f8-a8xxxxx",
         "run_url": "https://kubeflow.skit.ai/pipeline/?ns=...",
         "file_path": "/tmp/outputs/Output/data",
         "s3_path": "<artifact s3_path tar file>",
         "webhook": true
      }
   }

Error
^^^^^^
.. code-block:: json

   {
   "status": "error",
      "response": {
         "message": "Run failed.",
         "run_id": "662b9909-d251-45f8xxxxxxxx",
         "run_url": "https://kubeflow.skit.ai/pipeline/?ns=...",
         "file_path": null,
         "s3_path": null,
         "webhook": true
      }
   }

Pending
^^^^^^^
.. code-block:: json

   {
   "status": "pending",
      "response": {
         "message": "Run in progress.",
         "run_id": "662b9909-d251-45f8-axxxxxxxxx",
         "run_url": "https://kubeflow.skit.ai/pipeline/?ns=...",
         "file_path": null,
         "s3_path": null,
         "webhook": true
      }
   }


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
