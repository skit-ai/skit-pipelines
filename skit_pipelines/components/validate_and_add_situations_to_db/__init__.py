
import kfp

from skit_pipelines import constants as pipeline_constants

from skit_pipelines.types.situation_mapping_info import SituationMappingInfoResponseType

def validate_and_add_situations_to_db(situations: str, scenario: str , scenario_category: str) -> SituationMappingInfoResponseType:
    """
    Check if the situation exists in db, if exists return the id else insert the situation to db and return the id
    """
    from skit_pipelines.utils.db_utils import get_connections
    from skit_pipelines import constants as pipeline_constants
    from skit_pipelines.components.validate_and_add_situations_to_db.queries import CREATE_SITUATIONS_MAPPING_TABLE_QUERY, SEARCH_SITUATION_QUERY, INSERT_SITUATION_QUERY
    
    from skit_pipelines.types.situation_mapping_info import SituationMappingInfo
    from loguru import logger
    
    situations = [val.strip() for val in situations.split('::')]
    logger.info(f"Situations: {situations}")
    logger.info(f"scenario: {scenario}")
    logger.info(f"scenario_category: {scenario_category}")
    
    print("Dbname",pipeline_constants.ML_METRICS_DB_NAME)
    print("user",pipeline_constants.ML_METRICS_DB_USER )
    print("password",pipeline_constants.ML_METRICS_DB_PASSWORD )
    print("host",pipeline_constants.ML_METRICS_DB_HOST )
    print("port",pipeline_constants.ML_METRICS_DB_PORT )
    conn = get_connections(pipeline_constants.ML_METRICS_DB_NAME ,
                           pipeline_constants.ML_METRICS_DB_USER, 
                           pipeline_constants.ML_METRICS_DB_PASSWORD, 
                           pipeline_constants.ML_METRICS_DB_HOST, 
                           pipeline_constants.ML_METRICS_DB_PORT)
    
    id_val = ''
    situation_info_list = []
    
    # if db not present create it
    cur = conn.cursor()
    cur.execute(CREATE_SITUATIONS_MAPPING_TABLE_QUERY)
    conn.commit()
    
    
    for situation in situations:
        situation_info = {}
        situation = situation.lower()
        cur = conn.cursor()
        cur.execute(SEARCH_SITUATION_QUERY, (situation,))
        record = cur.fetchone()
        
        if record:
            id_val = record[0]
            logger.info(f"ID in table: {id_val}")
        else:
            
            scenario_category = scenario_category.upper()
            scenario = scenario.lower()
    
            query_parameters = {"situation": situation, "scenario": scenario,  "scenario_category" :scenario_category}
            cur.execute(INSERT_SITUATION_QUERY, query_parameters)
            id = cur.lastrowid
            id_val = id 
            
        situation_info['situation_id'] = id_val
        situation_info['situation'] = situation
        situation_info['scenario'] = scenario
        situation_info['scenario_category'] = scenario_category
        situation_info_list.append(situation_info)
        
    logger.info(f"situation_info: {situation_info_list}")
    conn.commit()
    cur.close()
    conn.close()
        
    response = SituationMappingInfo(situation_info_list)
    
    logger.info(f"situation_info_list: {situation_info_list}")
    logger.info(f"response: {response}")
    return response
        
        
validate_and_add_situations_to_db_op = kfp.components.create_component_from_func(
   validate_and_add_situations_to_db, base_image=pipeline_constants.BASE_IMAGE
)