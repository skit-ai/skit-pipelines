UPDATE_IS_VALID_SITUATION = """
    UPDATE situation_scenario_mapper
    SET is_valid = FALSE
    WHERE id = %s;
"""