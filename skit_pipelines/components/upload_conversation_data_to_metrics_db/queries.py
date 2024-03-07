CREATE_GENERATED_CONVERSATIONS_QUERY = """
    CREATE TABLE IF NOT EXISTS generated_conversations
    (
        id SERIAL PRIMARY KEY,
        situation_id INT NOT NULL,
        client_id INT,
        template_id INT,
        prompt_id INT NOT NULL,
        generated_conversations_s3_link VARCHAR(511),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT fk_prompt_id FOREIGN KEY (prompt_id) REFERENCES prompt_details(id) ON DELETE CASCADE ON UPDATE CASCADE,
        CONSTRAINT fk_situation_id FOREIGN KEY (situation_id) REFERENCES situation_scenario_mapper(id) ON DELETE CASCADE ON UPDATE CASCADE
    );
    """

CREATE_PROMPT_TABLE_QUERY = """
    CREATE TABLE IF not EXISTS prompt_details
    (
        id SERIAL PRIMARY KEY,
        client_id INT,
        template_id INT,
        links_to_prompt_in_s3 VARCHAR(511),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    
INSERT_GENERATED_CONVERSATIONS_QUERY  = """INSERT INTO generated_conversations 
    (
        situation_id,
        client_id,
        template_id,
        prompt_id,
        generated_conversations_s3_link,
        project_name
    )
    VALUES
    (
        %(situation_id)s,
        %(client_id)s,
        %(template_id)s,
        %(prompt_id)s,
        %(generated_conversations_s3_link)s,
        %(project_name)s
    ) 
    RETURNING id;
    """


INSERT_PROMPT_DATA  = """INSERT INTO prompt_details 
    (
        client_id,
        template_id,
        links_to_prompt_in_s3
    )
    VALUES
    (
        %(client_id)s,
        %(template_id)s,
        %(links_to_prompt_in_s3)s
    )
    RETURNING id;
    """    


SEARCH_PROMPT_QUERY = """SELECT id FROM prompt_details WHERE 
links_to_prompt_in_s3 = %s;
"""