from typing import Callable, Dict, List
import yaml

import skit_pipelines.constants as const
import skit_pipelines.pipelines as pipelines


def get_config(path):
    with open(path, 'r') as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

class Config:
    
    @classmethod
    def load(cls) -> 'Config':
        config = cls()
        config.RUN_NAME_MAP = config.get_run_name_map()
        config.PIPELINE_FN_MAP = config.get_pipeline_fn_map()
        config.KAFKA_TOPIC_MAP = config.get_publisher_topic_map()
        return config
    
    def __init__(self, path=const.CONFIG_FILE_PATH):
        self.config = get_config(path)
    
    def get_pipeline_configs(self) -> Dict[str, str]:
        return self.config['pipelines']
    
    def get_pipeline_names(self) -> List[str]:
        return list(self.get_pipeline_configs())
    
    def get_publisher_topics(self) -> List[str]:
        return self.config['publisher_topics']
    
    def get_run_name_map(self) -> Dict[str, str]:
        return {
            pipeline_name: pipeline_config['default_run'] \
                for pipeline_name, pipeline_config in self.get_pipeline_configs().items()
        }
    
    def get_pipeline_fn_map(self) -> Dict[str, Callable]:
        return {
            pipeline_name: self.get_pipeline_fn(pipeline_config['main_function']) \
                for pipeline_name, pipeline_config in self.get_pipeline_configs().items()
        }
    
    def get_publisher_topic_map(self) -> Dict[str, str]:
        return {
            pipeline_name: pipeline_config['topic'] \
                for pipeline_name, pipeline_config in self.get_pipeline_configs().items()
        }
    
    def valid_pipeline(self, name: str) -> bool:
        return name in self.get_pipeline_names()
        
    @staticmethod
    def get_pipeline_fn(name: str) -> Callable:
        try:
            return getattr(pipelines, name)
        except AttributeError:
            raise AttributeError(f"Pipeline {name} does not exist, please check the name or create one first.")


config = Config.load()