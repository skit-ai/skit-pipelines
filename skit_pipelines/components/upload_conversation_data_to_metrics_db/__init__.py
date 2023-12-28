
import kfp
from kfp.components import OutputPath

from skit_pipelines import constants as pipeline_constants

from typing import List, Dict

def upload_conversation_data_to_metrics_db(situations_id_info: List[Dict[str, str]], client_id: str ,template_id: str,  generated_conversations_s3_link: str, prompt_links_in_s3: str) :
    """
    Upload the conversation data to metrics DB
    """
    from skit_pipelines.utils.db_utils import get_connections
    import skit_pipelines.constants as const
    from skit_pipelines.components.upload_conversation_data_to_metrics_db.queries import CREATE_GENERATED_CONVERSATIONS_QUERY, CREATE_PROMPT_TABLE_QUERY, INSERT_GENERATED_CONVERSATIONS_QUERY, INSERT_PROMPT_DATA, SEARCH_PROMPT_QUERY
    from loguru import logger


    conn = get_connections(const.ML_METRICS_DB_NAME ,
                           const.ML_METRICS_DB_USER, 
                           const.ML_METRICS_DB_PASSWORD, 
                           const.ML_METRICS_DB_HOST, 
                           const.ML_METRICS_DB_PORT)
    
    # if generated_conversations table not present create it
    cur = conn.cursor()
    cur.execute(CREATE_GENERATED_CONVERSATIONS_QUERY)
    conn.commit()
    
    # if prompt_details table not present create it
    cur.execute(CREATE_PROMPT_TABLE_QUERY)
    conn.commit()
    
    # search for prompt in prompt table
    cur = conn.cursor()
    cur.execute(SEARCH_PROMPT_QUERY, (prompt_links_in_s3,))
    record = cur.fetchone()
    if record:
        prompt_id = record[0]
    else: 
        cur.execute(INSERT_PROMPT_DATA ,{"client_id": client_id,"template_id": template_id, "links_to_prompt_in_s3" :prompt_links_in_s3})
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