def prepare_crr_df(untagged_records_path_on_disk, org_id, given_comma_seperated_columns):
    import pandas as pd
    
    df = pd.read_csv(untagged_records_path_on_disk)
    uuids = df.call_uuid.unique()
    console_links = [
        f"https://console.vernacular.ai/{org_id}/call-report/#/call?uuid={i}"
        for i in uuids
    ]
    
    df_crr = pd.DataFrame(columns= ["call_url"])
    if given_comma_seperated_columns:
        columns = given_comma_seperated_columns.split(",")
        if "call_url" not in columns:
            columns.insert(0, "call_url")
        
    df_crr.columns = columns
    df_crr["call_url"] = console_links

    return df_crr
