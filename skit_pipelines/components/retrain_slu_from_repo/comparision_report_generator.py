import pandas as pd
from tabulate import tabulate


def comparison_classification_report(
        report1_path: str, report2_path: str, output_path: str
):
    report1_df = pd.read_csv(report1_path)

    if not report2_path:
        report2_df = pd.DataFrame(
            columns=["Unnamed: 0", "precision", "recall", "f1-score", "support"],
            index=range(len(report1_df)),
        )
    else:
        report2_df = pd.read_csv(report2_path)

    # Extract the class labels from both reports
    classes1 = report1_df["Unnamed: 0"].tolist()
    classes2 = report2_df["Unnamed: 0"].tolist()

    # Create a set of all class labels
    all_classes = classes1 + [x for x in classes2 if x not in classes1]
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
        index1 = (
            report1_df[report1_df["Unnamed: 0"] == class_label].index[0]
            if class_label in classes1
            else None
        )
        index2 = (
            report2_df[report2_df["Unnamed: 0"] == class_label].index[0]
            if class_label in classes2
            else None
        )

        # Get the precision, recall, f1-score, and support values for each report
        precision1 = report1_df["precision"][index1] if index1 is not None else None
        recall1 = report1_df["recall"][index1] if index1 is not None else None
        f1_score1 = report1_df["f1-score"][index1] if index1 is not None else None
        support1 = int(report1_df["support"][index1]) if index1 is not None else None

        precision2 = report2_df["precision"][index2] if index2 is not None else None
        recall2 = report2_df["recall"][index2] if index2 is not None else None
        f1_score2 = report2_df["f1-score"][index2] if index2 is not None else None
        support2 = int(report2_df["support"][index2]) if index2 is not None else None

        # Create tuples of values for each metric
        precision_tuple = (precision1, precision2)
        recall_tuple = (recall1, recall2)
        f1_score_tuple = (f1_score1, f1_score2)
        support_tuple = (support1, support2)

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
