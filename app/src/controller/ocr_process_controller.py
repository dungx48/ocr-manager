from fastapi import APIRouter, Request
from fastapi import File, UploadFile

from src.service.ocr_process_service import OcrProcessService
from src.common.base.structural.response_object import ResponseObject

ocr_process_router = APIRouter(
    prefix="/ocr-process",
    tags=["OcrProcess"]
)

ocr_process_service = OcrProcessService()

@ocr_process_router.post("/", response_model=dict, summary="OCR from image")
def ocr_process(request: Request, image: UploadFile = File(...)):
    """
    POST :IMG:
    """
    try:
        data_result = ocr_process_service.ocr_process(image)
        return ResponseObject().success(data_result=data_result['ocr_result'], path=request.url.__str__())
    except Exception as e:
        return ResponseObject().error(error=str(e), path=request.url.__str__())