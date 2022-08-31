

def main(data_path):
    import pandas as pd
    from eevee.metrics import entity_report
    
    df = pd.read_csv(data_path)
    
    truth_df = df[["data_id", "truth_entities_with_duckling"]]
    pred_df = df[["data_id", "predicted_entities_with_modifications"]]

    truth_df.rename(columns={
        "data_id": "id",
        "truth_entities_with_duckling": "entities",
    }, inplace=True)

    pred_df.rename(columns={
        "data_id": "id",
        "predicted_entities_with_modifications": "entities",
    }, inplace=True)

    print(truth_df.columns)
    print(pred_df.columns)

    op = entity_report(truth_df, pred_df)
    print(op)


# if __name__ == "__main__":

#     main("duck_4284.csv")
    # main("duck_4333.csv")

