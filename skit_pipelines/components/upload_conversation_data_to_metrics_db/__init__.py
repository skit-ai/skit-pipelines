
import kfp
from kfp.components import InputPath

from skit_pipelines import constants as pipeline_constants

from typing import List, Dict

def upload_conversation_data_to_metrics_db(situations_id_info: List[Dict[str, str]], client_id: str ,template_id: str,  
                                           generated_conversations_s3_link: str, 
                                           prompt_links_in_s3: str, conv_directory:  InputPath(str)) :
    """
    Upload the conversation data to metrics DB
    """
    from skit_pipelines.components.upload_conversation_data_to_metrics_db.queries import CREATE_GENERATED_CONVERSATIONS_QUERY, CREATE_PROMPT_TABLE_QUERY, SEARCH_PROMPT_QUERY, INSERT_PROMPT_DATA,  INSERT_GENERATED_CONVERSATIONS_QUERY
    from loguru import logger
    import psycopg2
    from skit_pipelines.components.upload_conversation_data_to_metrics_db.utils import get_file_path_from_folder
    from skit_pipelines import constants as pipeline_constants

    def upload_file_to_s3(
        path_on_disk: InputPath(str),
        upload_path: str = "",
        bucket: str = ""
    ) -> str:
        import boto3
        from loguru import logger
        
        s3_resource = boto3.client("s3")
        
        s3_resource.upload_file(path_on_disk, bucket, upload_path)
        
        s3_path = f"s3://{bucket}/{upload_path}"
        logger.debug(f"Uploaded {path_on_disk} to {upload_path}")
        return s3_path

    
    conn = psycopg2.connect(
        dbname=pipeline_constants.ML_METRICS_DB_NAME,
        user=pipeline_constants.ML_METRICS_DB_USER,
        password=pipeline_constants.ML_METRICS_DB_PASSWORD,
        host=pipeline_constants.ML_METRICS_DB_HOST,
        port=pipeline_constants.ML_METRICS_DB_PORT,
    )
    
    prompt_s3_path = None
    s3_prompt_dir_name  = f'pipeline_uploads/prompt/global_prompt.txt'
    
    if not prompt_links_in_s3:
        prompt_local_path = get_file_path_from_folder(conv_directory, 'prompt.txt')
        prompt_s3_path = upload_file_to_s3(
                path_on_disk=prompt_local_path,
                upload_path=s3_prompt_dir_name,
                bucket=pipeline_constants.KUBEFLOW_SANDBOX_BUCKET
                )
        
        logger.info(f"Prompt local path: {prompt_local_path}")
    else:
        prompt_s3_path = prompt_links_in_s3
    
    logger.info(f"Prompt s3 path: {prompt_s3_path}")
    # if generated_conversations table not present create it
    cur = conn.cursor()
    
    # if prompt_details table not present create it
    cur.execute(CREATE_PROMPT_TABLE_QUERY)
    conn.commit()
    
    logger.info(f"generated_conversations_s3_link, {generated_conversations_s3_link}")
    cur.execute(CREATE_GENERATED_CONVERSATIONS_QUERY)
    conn.commit()
    
    # search for prompt in prompt table
    cur = conn.cursor()
    cur.execute(SEARCH_PROMPT_QUERY, (prompt_s3_path,))
    record = cur.fetchone()
    if record:
        prompt_id = record[0]
    else: 
        query_parameters_1 = {"client_id": client_id,"template_id": template_id, "links_to_prompt_in_s3" :prompt_s3_path}
        cur.execute(INSERT_PROMPT_DATA ,query_parameters_1)
        conn.commit()
        prompt_id = cur.fetchone()[0]
        
    logger.info(f"Records inserted to Prompt details table. Auto id : {prompt_id} ")


    for data in situations_id_info:
        situation_id = data['situation_id']
        cur = conn.cursor()
        query_parameters_2 = { "situation_id": situation_id, 
                                "client_id": client_id, 
                                "template_id": template_id,
                                "prompt_id": prompt_id,
                                "generated_conversations_s3_link" :generated_conversations_s3_link
                                }
        cur.execute(INSERT_GENERATED_CONVERSATIONS_QUERY ,query_parameters_2)
        conn.commit()
        generated_conv_id = cur.fetchone()[0]
        
        logger.info(f"Records inserted to generated_conversations table. Auto id : {generated_conv_id} ")
        
    cur.close()
    conn.close()
    
    
upload_conversation_data_to_metrics_db_op= kfp.components.create_component_from_func(
    upload_conversation_data_to_metrics_db, base_image=pipeline_constants.BASE_IMAGE
)