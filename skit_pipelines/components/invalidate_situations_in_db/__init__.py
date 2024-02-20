
import kfp

from skit_pipelines import constants as pipeline_constants

def invalidate_situations_in_db(situation_id):
    """
    Check if the situation exists in db, if exists return the id else insert the situation to db and return the id
    """
    from skit_pipelines import constants as pipeline_constants
    from skit_pipelines.components.invalidate_situations_in_db.queries import UPDATE_IS_VALID_SITUATION
    
    from loguru import logger
    import psycopg2
    
    situation_id_list = [int(val.strip()) for val in situation_id.split(',')]
    
    logger.info(f"Situation id list: {situation_id_list}")
    
    conn = psycopg2.connect(
        dbname=pipeline_constants.ML_METRICS_DB_NAME,
        user=pipeline_constants.ML_METRICS_DB_USER,
        password=pipeline_constants.ML_METRICS_DB_PASSWORD,
        host=pipeline_constants.ML_METRICS_DB_HOST,
        port=pipeline_constants.ML_METRICS_DB_PORT,
    )
    
    for id_value in situation_id_list:
        cur = conn.cursor()
        cur.execute(UPDATE_IS_VALID_SITUATION, (id_value,))
        conn.commit()
        
    cur.close()
    conn.close()

invalidate_situations_in_db_op = kfp.components.create_component_from_func(
    invalidate_situations_in_db, base_image=pipeline_constants.BASE_IMAGE
)