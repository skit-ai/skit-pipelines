from typing import List, Dict, Any
import json
import requests
from kafka import KafkaConsumer

# ConsumerRecord(topic='data-pipeline', partition=0, offset=0, timestamp=1651317435380, timestamp_type=0, key=None, value=b'{"status":"ok",...}', headers=[], checksum=None, serialized_key_size=-1, serialized_value_size=341, serialized_header_size=-1)

# example Kafka Consumer 
consumer = KafkaConsumer(
    'data-pipeline',
    'model-train-pipeline',
    bootstrap_servers='localhost:19092',
    auto_offset_reset='latest'
)
for message in consumer:
    print(json.loads(message.value))


def start_consumer(
    topics: List[str],
    bootstrap_servers: List[str],
    auto_offset_reset: str ='latest'
) -> KafkaConsumer:
    """
    Start a Kafka consumer
    """
    consumer = KafkaConsumer(
        *topics,
        bootstrap_servers=bootstrap_servers,
        auto_offset_reset=auto_offset_reset
    )
    return consumer


def send_finished_runs(url_path: str, data: Dict[str, Any]):
    """
    Send finished runs to the server
    """
    
    response = requests.post(url_path, json=data)
    return response

def consume_finished_runs(consumer: KafkaConsumer):
    for message in consumer:
        send_finished_runs(message.value)