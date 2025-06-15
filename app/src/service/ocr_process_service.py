import os
import ast
import json
from time import sleep
from decouple import config
from uuid import uuid4
from datetime import datetime
from fastapi import UploadFile
from kafka import KafkaProducer
from confluent_kafka import Consumer

class OcrProcessService():
    application_enable = True
    def __init__(self):
        self.start_time = datetime.now().isoformat()
        self.save_dir = config('SAVE_IMG')


        kafka_servers = config('KAFKA_BOOTSTRAP_SERVERS')
        self.request_topic = config('KAFKA_OCR_REQUEST_TOPIC')

        # Khởi tạo producer
        self.producer = KafkaProducer(
            bootstrap_servers=kafka_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )

        # Khởi tạo consumer
        conf = {
            'bootstrap.servers': config("KAFKA_BOOTSTRAP_SERVERS"),
            'group.id': config("KAFKA_GROUP_ID"),
            'auto.offset.reset': 'smallest',
            'partition.assignment.strategy': 'roundrobin'
        }
        self.consumer = Consumer(conf)
        self.topics_consume = config("KAFKA_OCR_RESPONSE_TOPIC").split(",")


    def ocr_process(self, image: UploadFile) -> dict:
        # Lưu ảnh
        msg_id = str(uuid4().hex)
        img_path = self.save_img(image=image, msg_id=msg_id)
        # Produce path ảnh qua Kafka
        self.build_msg_produce_to_kafka(msg_id, img_path)
        
        # Consume kết quả từ Kafka về và trả response
        msg_result = self.comsume_msg_from_kafka(msg_id)
        return msg_result
    
    def save_img(self, image: UploadFile, msg_id: str) -> str:
        # Đường dẫn thư mục lưu ảnh
        os.makedirs(self.save_dir, exist_ok=True)
        
        # Đọc nội dung ảnh và tạo tên file
        content = image.file.read()
        base_name, ext = os.path.splitext(image.filename)
        filename = f"{base_name}_{msg_id}{ext}"
        path = os.path.join(self.save_dir, filename)

        # Ghi file vào đường dẫn đã tạo
        with open(path, 'wb') as f:
            f.write(content)

        return path
        
    def build_msg_produce_to_kafka(self, msg_id:str, img_path:str):
        payload = {
            "msg_id": msg_id,
            'image_path': img_path,
            "metadata": {
                "user_id": None,
                "document_type": "image",
                "priority": None
            },
            "options": {
                "language": "vie",
                "detect_table": False
            },
            "created_at": self.start_time
        }
        self.producer.send(self.request_topic, payload)
        self.producer.flush()
    
    def comsume_msg_from_kafka(self, msg_id) -> dict:
        try:
            self.consumer.subscribe(self.topics_consume)
            while self.application_enable:
                msg = self.consumer.poll(timeout=1.0)
                if msg is None:
                    continue
                json_message = self.get_json_message(msg)
                if msg_id == json_message['msg_id']:
                    return json_message
        finally:
            self.consumer.close()

    def get_json_message(self, msg):
        try:
            json_message = ast.literal_eval(msg.value().decode('utf8'))
        except ValueError:
            json_message = json.loads(msg.value().decode('utf8'))
        except Exception as e:
            raise Exception(f"message {str(e)} error")
        if not isinstance(json_message, dict):
            raise Exception(f'message -{str(json_message)}-is not JSON ')
        return json_message
    
    def job_archive_img():
        pass