import ast
import json
import socket
import time
from concurrent.futures.thread import ThreadPoolExecutor

import decouple
from confluent_kafka import Producer


class BaseKafkaProducer:
    def __init__(self, ip, port, **kwargs):
        self.ip = ip
        self.port = port
        self.executor = ThreadPoolExecutor(int(decouple.config('KAFKA_THREAD_POOL_PRODUCER_SIZE')))
        self.config = {'bootstrap.servers': ','.join(
            [str(ip + ':' + p) for ip, p in zip(self.ip.split(','), self.port.split(','))]),
            'client.id': socket.gethostname(),
            'reconnect.backoff.ms': 1000,
            'request.timeout.ms': 40000,
            'acks': 'all',
            'retries': 15,
            'retry.backoff.ms': 1000,
            'max.in.flight.requests.per.connection': 1,
            'compression.type': "lz4"
        }
        if hasattr(kwargs, "configs"):
            self.config = kwargs.get('configs')
        self.producer = Producer(self.config)

    def send(self, topic: str, message: dict, flush=False, key=None, headers=None, partition=None, timestamp_ms=None):
        try:
            self.producer.produce(topic, json.dumps(message, indent=4), callback=self.acked)
            self.producer.poll(0)
            time.sleep(0.01)
            if flush:
                self.producer.flush()
        except Exception as ee:
            print("Send Error: {}".format(ee.__str__()))

    def acked(self, error, message):
        if error is not None:
            print("Send Error: {} - {}".format(str(error), message.value().decode('utf-8')))
            try:
                jmess = ast.literal_eval(message.value().decode('utf-8'))
                self.on_error(error, jmessage=jmess)
            except Exception as ee:
                print(ee.__str__())
        else:
            try:
                jmess = ast.literal_eval(message.value().decode('utf-8'))
                self.on_success(message, jmessage=jmess)
            except Exception as ee:
                print(ee.__str__())

    @staticmethod
    def on_success(message, **args):
        print("Send Success: {} ".format(str(args.get("jmessage"))))

    @staticmethod
    def on_error(message, **args):
        print("Send Error: {} - {} ".format(str(message.__str__()), str("jmessage")))
