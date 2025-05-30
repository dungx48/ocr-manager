from fastapi import FastAPI

from app.src.common.config.log_config import CustomizeLogger

app = FastAPI(docs_url=None, redoc_url=None)

logger = CustomizeLogger.make_logger

app.logger = logger