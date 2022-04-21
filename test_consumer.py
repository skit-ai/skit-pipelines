import json 
from kafka import KafkaConsumer


if __name__ == '__main__':
    # example Kafka Consumer 
    consumer = KafkaConsumer(
        'data-pipeline',
        bootstrap_servers='localhost:19092',
        auto_offset_reset='earliest'
        # auto_offset_reset='latest'
    )
    for message in consumer:
        print(json.loads(message.value))