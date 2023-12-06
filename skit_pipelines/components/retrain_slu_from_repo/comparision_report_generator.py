import pandas as pd
from tabulate import tabulate

"""
    This file contains functionality for combining classification report and confusion matrix from two different
    models and provide a unified file that makes it easier to compare the model performances. Each function takes
    2 input Csv file paths and outputs the path to a single Csv file containing the comparison.
"""


def _get_index(df, column_name):
    if column_name in df["Unnamed: 0"].values:
        return df[df["Unnamed: 0"] == column_name].index[0]
    return None


def _get_value(df, column_name, index):
    if column_name in df and index:
        return df.loc[index, column_name]
    return None


def comparison_classification_report(report1_path: str, report2_path: str, output_path: str):
    report1_df = pd.read_csv(report1_path)

    if not report2_path:
        # If report2_path is empty, generate a report only for the first dataset
        comparison_df = pd.DataFrame(report1_df)
        comparison_df.to_csv(output_path, index=False)
        print(tabulate(comparison_df, headers="keys", tablefmt="psql"))
        return

    report2_df = pd.read_csv(report2_path)

    # Extract the class labels from both reports
    classes1 = report1_df["Unnamed: 0"].tolist()
    classes2 = report2_df["Unnamed: 0"].tolist()

    # Create a set of all class labels
    all_classes = list(set(classes1).union(classes2))
    all_classes = [x for x in all_classes if not pd.isna(x)]

    # Move "accuracy", "macro avg", and "weighted avg" to the end
    special_rows = ["accuracy", "macro avg", "weighted avg"]
    for special_row in special_rows:
        if special_row in all_classes:
            all_classes.remove(special_row)
        all_classes.append(special_row)

    # Initialize a dictionary to store the comparison data
    comparison_data = {}

    # Iterate through each class label
    for class_label in all_classes:
        # Get the row index for each class label
        index1 = _get_index(report1_df, class_label)
        index2 = _get_index(report2_df, class_label)

        # Create tuples of values for each metric
        precision_tuple = (_get_value(report1_df, "precision", index1), _get_value(report2_df, "precision", index2))
        recall_tuple = (_get_value(report1_df, "recall", index1), _get_value(report2_df, "recall", index2))
        f1_score_tuple = (_get_value(report1_df, "f1-score", index1), _get_value(report2_df, "f1-score", index2))
        support_tuple = (_get_value(report1_df, "support", index1), _get_value(report2_df, "support", index2))

        # Store the tuples in the comparison data dictionary
        comparison_data[class_label] = (
            precision_tuple,
            recall_tuple,
            f1_score_tuple,
            support_tuple,
        )

    # Create a DataFrame from the comparison data
    comparison_df = pd.DataFrame.from_dict(
        comparison_data,
        orient="index",
        columns=["precision", "recall", "f1-score", "support"],
    )

    comparison_df.to_csv(output_path)
    # Print the comparison report using tabulate for better formatting
    print(tabulate(comparison_df, headers="keys", tablefmt="psql"))


def comparison_confusion_report(
        latest_model_path: str, prod_model_path: str, output_path: str
):
    latest_df = pd.read_csv(latest_model_path)
    prod_df = pd.read_csv(prod_model_path) if prod_model_path else pd.DataFrame(columns=["Unnamed: 0"])

    labels_latest = latest_df['Unnamed: 0'].to_list()
    labels_prod = prod_df['Unnamed: 0'].to_list() if 'Unnamed: 0' in prod_df.columns else []
    labels_common = list(set(labels_latest).union(labels_prod))
    comparison_data = {}

    for column in labels_common:
        index_latest = _get_index(latest_df, column)
        index_prod = _get_index(prod_df, column)
        comparison_values = []
        for inner_column in labels_common:
            comparison_values.append(
                (_get_value(latest_df, inner_column, index_latest), _get_value(prod_df, inner_column, index_prod)))
        comparison_data[column] = comparison_values

    comparison_df = pd.DataFrame.from_dict(
        comparison_data,
        orient="index",
        columns=labels_common,
    )
    comparison_df.to_csv(output_path)
