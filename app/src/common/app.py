from fastapi import FastAPI

from app.src.common.config.log_config import CustomizeLogger

app = FastAPI()

logger = CustomizeLogger.make_logger()

app.logger = logger