import logging
from concurrent.futures.thread import ThreadPoolExecutor

from starlette.middleware.cors import CORSMiddleware
from starlette_prometheus import PrometheusMiddleware

from app.src.common.app import app
from app.src.controller.controller import Controller

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(PrometheusMiddleware)

kafka_consumer = Controller()


# @app.on_event("startup")
# def startup_event():
#     logging.info("[APP-WORKER] on startup event....")
#     pool = ThreadPoolExecutor(max_workers=2)
#     # kafka_consumer.start()


# @app.on_event("shutdown")
# def shutdown_event():
#     logging.warning("[APP] running on shutdown event....")
#     # kafka_consumer.stop_application()
