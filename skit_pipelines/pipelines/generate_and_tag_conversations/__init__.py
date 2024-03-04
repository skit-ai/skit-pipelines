import kfp
from kfp.components import OutputPath
from typing import Optional

from skit_pipelines import constants as pipeline_constants
from skit_pipelines.components import (
    upload2s3_op,
    zip_file_and_notify_op,
    slack_notification_op,
    validate_and_add_situations_to_db_op,
    final_conversation_generator_op,
    upload_conv_to_label_studio_op,
    upload_conversation_data_to_metrics_db_op,
)


@kfp.dsl.pipeline(
    name="Generate and tag conversations",
    description="Generate final conversations based on the situation data provided and upload it to labelstudio for tagging",
)
def generate_and_tag_conversations(
    *,
    situations: str = "",
    scenario: str = "",
    scenario_category: str = "",
    s3_links_to_prompts: str = "",
    llm_trainer_repo_name: str = "LLMtrainer",
    llm_trainer_repo_branch: str = "main",
    model: str = 'gpt-4',
    n_iter: int = 1,
    n_choice: int = 2,
    temperature: float = 0.99,
    client_id: str,
    template_id: str,
    labelstudio_project_id: str,
    data_label: str = "",
    project_name: str = "",
    notify: str = "",
    channel: str = "",
    slack_thread: str = ""
    ):
    """
    A pipeline to generate and tag conversations given a situation
    
    .. _p_generate_and_tag_conversations:

    Example payload to invoke via slack integrations:

    A minimal example:

        @charon run generate_and_tag_conversations

        .. code-block:: python

            {   "situations" : "The user disputes the debt, so the agent transfers the call to the agent :: The user cannot pay any amount as they have a difficult situation, so the agent hangs up the call. ",
                "scenario" : "Test scenario",
                "scenario_category" : "Test scenario category",
                "llm_trainer_repo_branch" : "refactor-data-gen-script",
                "client_id" : "85",
                "template_id" : "0",
                "labelstudio_project_id" : "95",
                "s3_links_to_prompts": "s3://kubeflow-us-cluster/pipeline_uploads/prompt/test_prompt.txt",
                "data_label" : "UAT",
                "project_name" : "test project name"
            }


    A full available parameters example:

        @charon run generate_and_tag_conversations

        .. code-block:: python

            {   "situations" : "The user disputes the debt, so the agent transfers the call to the agent :: The user cannot pay any amount as they have a difficult situation, so the agent hangs up the call. ",
                "scenario" : "Test scenario",
                "scenario_category" : "Test scenario category",
                "llm_trainer_repo_branch" : "refactor-data-gen-script",
                "client_id" : "85",
                "template_id" : "0",
                "labelstudio_project_id" : "95",
                "s3_links_to_prompts": "s3://kubeflow-us-cluster/pipeline_uploads/prompt/test_prompt.txt",
                "data_label" : "UAT",
                "project_name" : "test project name"
            }
    
    :param situations: The situations for generating the conversations, use delimiter :: to pass multiple situations
    :type situations: optional

    :param scenario: The scenario linked to the situation
    :type scenario: optional
    
    :param scenario_category: The scenarios category
    :type scenario_category: optional
    
    :param prompt: Prompt to the model for data generation
    type prompt: str
    
    :param s3_links_to_prompts: s3 links to the prompt to the model for data generation
    :type s3_links_to_prompts: str
    
    :param output_dir: The output directory where the generated conversations gets stored
    :type output_dir: str

    :param filename: Acts as a prfix to the default naming used
    :type filename: str

    :param llm_trainer_repo_name: The conversation generation repo name in Github.
    :type llm_trainer_repo_name: str
    
    :param llm_trainer_repo_branch: The branch name in the conversation generation repo to use , defaults to main.
    :type llm_trainer_repo_branch: str, optional
    
    :param model: Optional model to be used for generating data 
    :type model: str
    
    :param n_iter: No of times we make iterate on scenarios list to generate conversations
    type n_iter: int
    
    :param n_choice: No of convs generated in a single time from a scenario.
    type n_choice: int
    
    :param temperature: Temperature
    type temperature: float
    
    :param client_id: id of the client for which data is being generated
    :type client_id : str
    
    :param template_id: template id for which data is being generated
    :type template_id : str
    
    :param project_name: project name to distinguish between various experiments
    :type project_name : str
    
    :param notify: Whether to send a slack notification, defaults to ""
    :type notify: str, optional

    :param channel: The slack channel to send the notification, defaults to ""
    :type channel: str, optional

    :param slack_thread: The slack thread to send the notification, defaults to ""
    :type slack_thread: str, optional

    """
    
    validate_situations = validate_and_add_situations_to_db_op(situations=situations,
                                                         scenario=scenario ,  
                                                         scenario_category=scenario_category)
    
    situations_id_info = validate_situations.outputs['situation_mapping_info']
    conv_s3_dir_name = f'llm_artifacts/generated_conversations/{client_id}_{template_id}'
    
    conv_generation_output= final_conversation_generator_op(situation_info_list=situations_id_info,
                                                        s3_links_to_prompts = s3_links_to_prompts,
                                                        n_iter=n_iter,
                                                        n_choice=n_choice,
                                                        temperature=temperature,
                                                        model=model,
                                                        llm_trainer_repo_name=llm_trainer_repo_name,
                                                        llm_trainer_repo_branch=llm_trainer_repo_branch,
                                                    )
    conversations_dir = conv_generation_output.outputs["output"]
        
    conversation_s3_upload = upload2s3_op(
            path_on_disk=conversations_dir,
            reference=conv_s3_dir_name,
            bucket=pipeline_constants.KUBEFLOW_SANDBOX_BUCKET,
            upload_as_directory=True,
            ext=""
        )

    tag_calls_output = upload_conv_to_label_studio_op(project_id=labelstudio_project_id, 
                                                      conversations_dir= conversations_dir, 
                                                      data_label=data_label, 
                                                      situations_id_info=situations_id_info)
    
    
    upload_df_sizes = tag_calls_output.outputs["df_sizes"]
    upload_errors = tag_calls_output.outputs["errors"] 
    
    
    with kfp.dsl.Condition(notify != "", "notify").after(conversation_s3_upload) as check1:
        notification_text_1 = f"Generated conversations are successfully uploaded to s3 for client_id  : {client_id}."
        code_block = f"aws s3 cp {conversation_s3_upload.output} ."
        prompt_s3_notif = slack_notification_op(
            message=notification_text_1,
            channel=channel,
            cc=notify,
            code_block=code_block,
            thread_id=slack_thread,
        )
        
        prompt_s3_notif.execution_options.caching_strategy.max_cache_staleness = (
            "P0D"  # disables caching
        )
        
        notification_text_2 = "Here is the ZIP file generated by the Generate Sample conversations Pipeline."
        zip_file_and_notify = zip_file_and_notify_op(
                    path_on_disk = conversations_dir, 
                    message = notification_text_2,
                    channel = channel,
                    thread_id = slack_thread,
                    file_title = 'generated_conversations',
                    file_name = 'generated_conversations.zip',
                    notify = notify,
                    display_sample = True,
                    ).after(prompt_s3_notif)
        
        zip_file_and_notify.execution_options.caching_strategy.max_cache_staleness = (
            "P0D"  # disables caching
        )
    
    with kfp.dsl.Condition(notify != "", "notify").after(tag_calls_output) as check2:

        notification_text = f"""Uploaded the {upload_df_sizes} conversations for tagging to {labelstudio_project_id=}."""
        
        notification_text += f"\nErrors: {upload_errors}" if upload_errors else ""

        task_no_cache = slack_notification_op(
            notification_text, channel=channel, cc=notify, thread_id=slack_thread
        )
        task_no_cache.execution_options.caching_strategy.max_cache_staleness = (
            "P0D"  # disables caching
        )

    with kfp.dsl.Condition(upload_errors == [], "upload_to_metrics_db").after(tag_calls_output) as check3:
        upload_to_metrics_db_op = upload_conversation_data_to_metrics_db_op(situations_id_info=situations_id_info, client_id=client_id,
                                                                            template_id=template_id, 
                                                                            generated_conversations_s3_link=conversation_s3_upload.output,
                                                                            prompt_links_in_s3=s3_links_to_prompts, conv_directory=conversations_dir, 
                                                                            project_name=project_name)
    

__all__ = ["generate_and_tag_conversations"]
