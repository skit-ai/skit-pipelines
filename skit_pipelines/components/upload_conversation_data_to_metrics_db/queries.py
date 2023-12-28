CREATE_GENERATED_CONVERSATIONS_QUERY = """
    CREATE TABLE IF not EXISTS generated_conversations
    (
        id SERIAL PRIMARY KEY,
        situation_id INT NOT NULL,
        client_id INT,
        template_id INT,
		prompt_id INT,
        generated_conversations_s3_link VARCHAR(511),
		created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		prompt_id INT REFERENCES prompt_details(id) ON DELETE CASCADE ON UPDATE CASCADE,
		situation_id INT REFERENCES situation_scenario_mapper(id) ON DELETE CASCADE ON UPDATE CASCADE,
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
        prompt_id
        generated_conversations_s3_link,
    )
    VALUES
    (
        %(situation_id)s,
        %(client_id)s,
        %(template_id)s,
        %(prompt_id)s,
        %(generated_conversations_s3_link)s
    ) """
    
    
INSERT_PROMPT_DATA  = """INSERT INTO prompt_details 
    (
        client_id,
        template_id,
        links_to_prompt_in_s3,
    )
    VALUES
    (
        %(client_id)s,
        %(template_id)s,
        %(links_to_prompt_in_s3)s
    ) """
    
SEARCH_PROMPT_QUERY = """SELECT id FROM prompt_details WHERE 
links_to_prompt_in_s3 = %s;
"""