
import kfp
from kfp.components import InputPath

from skit_pipelines import constants as pipeline_constants

from typing import List, Dict

def upload_conversation_data_to_metrics_db(situations_id_info: List[Dict[str, str]], client_id: str ,template_id: str,  
                                           generated_conversations_s3_link: str, 
                                           prompt_links_in_s3: str, conv_directory:  InputPath(str), conv_s3_dir_name: str) :
    """
    Upload the conversation data to metrics DB
    """
    import skit_pipelines.constants as const
    from skit_pipelines.components.upload_conversation_data_to_metrics_db.queries import CREATE_GENERATED_CONVERSATIONS_QUERY, CREATE_PROMPT_TABLE_QUERY, INSERT_GENERATED_CONVERSATIONS_QUERY, INSERT_PROMPT_DATA, SEARCH_PROMPT_QUERY
    from loguru import logger
    import psycopg2
    from skit_pipelines.components.upload_conversation_data_to_metrics_db.utils import get_file_path_from_folder
    from skit_pipelines.components import upload2s3


    conn = psycopg2.connect(const.ML_METRICS_DB_NAME ,
                           const.ML_METRICS_DB_USER, 
                           const.ML_METRICS_DB_PASSWORD, 
                           const.ML_METRICS_DB_HOST, 
                           const.ML_METRICS_DB_PORT)
    
    prompt_s3_path = None
    
    if not prompt_links_in_s3:
        prompt_local_path = get_file_path_from_folder(conv_directory, 'prompt.txt')
        prompt_s3_path = upload2s3(
            path_on_disk=prompt_local_path,
            reference = conv_s3_dir_name ,
            bucket=pipeline_constants.KUBEFLOW_BUCKET,
            ext=".txt"
        )
        logger.info(f"Prompt local path: {prompt_local_path}")
    else:
        prompt_s3_path = prompt_links_in_s3
    
    logger.info(f"Prompt s3 path: {prompt_s3_path}")
    # if generated_conversations table not present create it
    cur = conn.cursor()
    cur.execute(CREATE_GENERATED_CONVERSATIONS_QUERY)
    conn.commit()
    
    # if prompt_details table not present create it
    cur.execute(CREATE_PROMPT_TABLE_QUERY)
    conn.commit()
    
    # search for prompt in prompt table
    cur = conn.cursor()
    cur.execute(SEARCH_PROMPT_QUERY, (prompt_s3_path,))
    record = cur.fetchone()
    if record:
        prompt_id = record[0]
    else: 
        cur.execute(INSERT_PROMPT_DATA ,{"client_id": client_id,"template_id": template_id, "links_to_prompt_in_s3" :prompt_s3_path})
        prompt_id = cur.lastrowid
        
    logger.info(f"Records inserted to Prompt details table. Auto id : {prompt_id} ")

    conn.commit()
    cur.close()
    conn.close()
    
    for data in situations_id_info:
        sub_scenario_id = data['situation_id']
        cur = conn.cursor()
        cur.execute(INSERT_GENERATED_CONVERSATIONS_QUERY ,{"situation_id": sub_scenario_id, 
                                                           "client_id": client_id, 
                                                           "template_id": template_id,
                                                           "prompt_id": prompt_id,
                                                           "generated_conversations_s3_link" :generated_conversations_s3_link})

        generated_conv_id = cur.lastrowid
        conn.commit()
        cur.close()
        conn.close()
        logger.info(f"Records inserted to generated_conversations table. Auto id : {generated_conv_id} ")
    
upload_conversation_data_to_metrics_db_op= kfp.components.create_component_from_func(
    upload_conversation_data_to_metrics_db, base_image=pipeline_constants.BASE_IMAGE
)