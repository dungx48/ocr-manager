import datetime
import json
import logging
import socket
import sys
from pathlib import Path

import decouple
from loguru import logger
from starlette import status

from app.src.common.base.kafka.base_producer import BaseKafkaProducer
from app.src.common.base.structural.base_singleton import Singleton


class KafkaLogging(BaseKafkaProducer, metaclass=Singleton):
    def __init__(self):
        kafka_log_ip = decouple.config('KAFKA_LOGGING_IP')
        kafka_log_port = decouple.config('KAFKA_LOGGING_PORT')
        configs = {'bootstrap.servers': ','.join(
            [str(ip + ':' + p) for ip, p in zip(kafka_log_ip.split(','), kafka_log_port.split(','))]),
            'client.id': socket.gethostname(),
            'reconnect.backoff.ms': 1000,
            'request.timeout.ms': 5000,
            'acks': 'all',
            'retries': 5,
            'retry.backoff.ms': 1000,
            'max.in.flight.requests.per.connection': 1,
            'compression.type': "lz4"
        }
        super().__init__(kafka_log_ip, kafka_log_port, configs=configs)


class InterceptHandler(logging.Handler):
    loglevel_mapping = {
        50: 'CRITICAL',
        40: 'ERROR',
        30: 'WARNING',
        20: 'INFO',
        10: 'DEBUG',
        0: 'NOTSET',
    }
    filter_not_logging = ['DEBUG', 'NOTSET']
    loggingKafkaProducer = KafkaLogging()
    print(loggingKafkaProducer.config)

    def format_record(self, record):
        args = {}
        if type(record.args) is dict:
            args = record.args
            record.message = str(record.msg)
        message = {
            "time": str(record.asctime if hasattr(record, 'asctime') else record.created if hasattr(record,
                                                                                                    'asctime') else datetime.datetime.now()),
            "name": str(record.name if hasattr(record, 'name') else ""),
            "level": str(record.levelname if hasattr(record, 'levelname') else ""),
            "message": str(record.message if hasattr(record, 'message') else record.getMessage()),
            "duration": args.get('duration') if 'duration' in args.keys() else 0,
            "log_type": args.get('log_type') if 'log_type' in args.keys() else 'trace',
            "service_msg_id": args.get('service_msg_id') if 'service_msg_id' in args.keys() else '',
            "page": args.get('page') if 'page' in args.keys() else '',
            "bytes_in": args.get('bytes_in') if 'bytes_in' in args.keys() else 0,
            "bytes_out": args.get('bytes_out') if 'bytes_out' in args.keys() else 0
        }
        return message

    def logging_to_kafka(self, record):
        service_name = decouple.config('SERVICE_NAME')
        message = self.format_record(record)
        log_message = {
            "time": message.get('time'),
            "timestamp": datetime.datetime.now().timestamp(),
            "status": "on",
            "dest_ip": "",
            "log_type": message.get('log_type'),
            "source_ip": socket.gethostbyname(socket.gethostname()),
            "level": message.get('level'),
            "bytes_in": message.get('bytes_in'),
            "bytes_out": message.get('bytes_out'),
            "duration": message.get('duration'),
            "page": message.get('page'),
            "service_message_id": message.get('service_msg_id'),
            "full_data": {
                "log_src": message.get('name'),
                "message": message.get('message')
            },
            "service_name": service_name,
            "system": "UTILS_PDF_MCRS",
            "response_code": "OK" if message.get('level') == 'INFO' else 'EUTPDF_COOR_0001',
            "response_msg": "OK" if message.get('level') == 'INFO' else 'ERROR WHEN PROCESS',
            "type_system": "DC",
            "create_date": datetime.datetime.utcfromtimestamp(record.created).isoformat("T") + "Z"
        }
        self.loggingKafkaProducer.send(decouple.config('KAFKA_LOGGING_TOPIC'), log_message, flush=False)

    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except AttributeError:
            level = self.loglevel_mapping[record.levelno]
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        log = logger.bind(request_id='app', encoding='utf-8')
        if type(record.args) is dict:
            log.opt(
                depth=depth,
                exception=record.exc_info
            ).log(level, str(record.msg))
        else:
            log.opt(
                depth=depth,
                exception=record.exc_info
            ).log(level, record.getMessage())
        if record.levelname not in self.filter_not_logging:
            if not (hasattr(record, 'args') and len(record.args) == 5 and record.args[2].endswith('actuator/health')):
                self.logging_to_kafka(record)


class CustomizeLogger:

    @classmethod
    def make_logger(cls, config_path: Path = ''):

        config = cls.load_logging_config(config_path)
        logging_config = config.get('logger')

        logger = cls.customize_logging(
            logging_config.get('path'),
            level=logging_config.get('level'),
            retention=logging_config.get('retention'),
            rotation=logging_config.get('rotation'),
            format=logging_config.get('format')
        )
        return logger

    @classmethod
    def customize_logging(cls,
                          filepath: Path,
                          level: str,
                          rotation: str,
                          retention: str,
                          format: str
                          ):

        logger.remove()
        logger.add(
            sys.stdout,
            enqueue=True,
            backtrace=True,
            level=level.upper(),
            format=format
        )
        # logger.add(
        #     str(filepath),
        #     rotation=rotation,
        #     retention=retention,
        #     enqueue=True,
        #     backtrace=True,
        #     level=level.upper(),
        #     format=format,
        #     encoding='utf-8'
        # )
        logging.basicConfig(handlers=[InterceptHandler()], level=0)
        logging.getLogger("uvicorn.access").handlers = [InterceptHandler()]
        for _log in ['uvicorn',
                     'uvicorn.error',
                     'fastapi'
                     ]:
            _logger = logging.getLogger(_log)
            _logger.handlers = [InterceptHandler()]

        return logger.bind(request_id=None, method=None)

    @classmethod
    def load_logging_config(cls, config_path):
        try:
            with open(config_path, encoding='utf-8') as config_file:
                config = json.load(config_file)
        except:
            config = {
                "logger": {
                    "path": "./logs/",
                    "filename": "access.log",
                    "level": "info",
                    "rotation": "20 days",
                    "retention": "1 months",
                    "format": "<level>{level: <8}</level> <green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> request id: {extra[request_id]} - <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"

                }
            }
        return config
