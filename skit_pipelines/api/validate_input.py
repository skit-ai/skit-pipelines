import datetime

ALLOWED_PAST_DATE = 270

# TODO: Ideally this list should come from a universal source and not be hard-coded
SUPPORTED_LANG_CODES = ["en-US", "en", "hi", "ta", "te", "ma", "gu", "mr"]

"""
    Collection of checks for input parameters that are passed to various skit-pipelines.
    Ideally these should be on the level of pipelines but currently we start with keeping them universal.
    
    To add a check:
        1. Add a new function with the validation check (Do ensure that the param is actually present in the 
        payload before accessing the validation condition.)
        2. If validation fails, append the error to self.errors
        3. Call the validation function from validate_input_params()
"""


class ValidateInput:
    def __init__(self, payload, pipeline_name):
        self.payload = payload
        self.pipeline_name = pipeline_name
        self.errors = []

    def _validate_date(self, date):
        try:
            formatted_date = datetime.datetime.strptime(date, "%Y-%m-%d")
            current_date = datetime.datetime.now()
            if (current_date - formatted_date).days > ALLOWED_PAST_DATE:
                self.errors.append(f"Dates within the last 6 months are only allowed. {date} is older than that.\n")
        except ValueError as e:
            self.errors.append(f"Invalid date format: expected YYYY-MM-DD for {date} instead.\n")

    def _validate_start_date(self):
        if "start_date" not in self.payload:
            return
        self._validate_date(self.payload["start_date"])

    def _validate_end_date(self):
        if "end_date" not in self.payload:
            return
        self._validate_date(self.payload["end_date"])

    def _validate_lang_support(self):
        if "lang" not in self.payload:
            return
        if self.payload["lang"] not in SUPPORTED_LANG_CODES:
            self.errors.append(f"Support for language code {self.payload['lang']} is not present currently.\n")

    def _validate_repo_for_retrain_slu(self):
        if self.pipeline_name == "retrain_slu" and "repo_name" not in self.payload:
            self.errors.append(f"Parameter repo_name is required for slu_retraining to happen.\n")

    def _validate_label_studio_ids_for_fetch_n_tag_turns_calls(self):
        if self.pipeline_name == "fetch_n_tag_turns_and_calls" and \
                ("labelstudio_project_id" not in self.payload and "call_project_id" not in self.payload):
            self.errors.append(f"At least one of labelstudio_project_id or call_project_id must be provided.\n")
    
    def _validate_situation_present(self):
        if self.pipeline_name in ["generate_and_tag_conversations", "generate_sample_conversations"]  and "situations" not in self.payload:
            self.errors.append(f"At least one situation must be provided.\n")
    
    def _validate_generate_and_tag_conversations_params(self):
        if self.pipeline_name == "generate_and_tag_conversations":
            if "template_id" not in self.payload:
                self.errors.append(f"Parameter template_id required for generate_and_tag_conversations pipeline\n")
            if "client_id" not in self.payload:
                self.errors.append(f"Parameter client_id required for generate_and_tag_conversations pipeline\n")
            if "labelstudio_project_id" not in self.payload:
                self.errors.append(f"Parameter labelstudio_project_id required for generate_and_tag_conversations pipeline\n")
            if "scenario" not in self.payload:
                self.errors.append("Parameter scenario is mandatory for generate_and_tag_conversations pipeline\n")
            if "scenario_category" not in self.payload:
                self.errors.append("Parameter scenario_category is mandatory for generate_and_tag_conversations pipeline\n")
        
    def validate_input_params(self):
        # Universal checks
        self._validate_start_date()
        self._validate_end_date()
        self._validate_lang_support()

        # Pipeline specific checks
        self._validate_repo_for_retrain_slu()
        self._validate_label_studio_ids_for_fetch_n_tag_turns_calls()
        self._validate_situation_present()
        self._validate_generate_and_tag_conversations_params()
        
        return self.errors
