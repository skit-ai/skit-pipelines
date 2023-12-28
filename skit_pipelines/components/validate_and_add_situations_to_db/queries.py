CREATE_SITUATIONS_MAPPING_TABLE_QUERY = """
    CREATE TABLE IF not EXISTS situation_scenario_mapper
    (
        id SERIAL PRIMARY KEY,
        situation TEXT NOT NULL,
        scenario TEXT,
        scenario_category VARCHAR(511),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """

INSERT_SITUATION_QUERY = """INSERT INTO situation_scenario_mapper 
    (
        situation,
        scenario,
        scenario_category
    )
    VALUES
    (   
        %(situation)s,
        %(scenario)s,
        %(scenario_category)s
    )
    """    

SEARCH_SITUATION_QUERY = """SELECT id FROM situation_scenario_mapper WHERE 
situation = %s;
"""
