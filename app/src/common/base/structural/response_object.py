import datetime

from fastapi.encoders import jsonable_encoder
from fastapi import status
from starlette.responses import JSONResponse


class Pagination:
    def __init__(self, total=0, total_page=0, page_size=0, page_num=0, enable=False):
        self.total = total
        self.total_page = total_page
        self.page_size = page_size
        self.page_num = page_num
        self.enable = enable


class ResponseObject:

    def __init__(self):
        super().__init__()
        self.timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def success(
            self, 
            client_message_id=None,
            status_code=status.HTTP_200_OK,
            data_result=None, 
            data_pagination=None, 
            error=None, 
            path=None
        ):
        
        self.client_message_id = client_message_id
        self.data = {'result': data_result, 'pagination': data_pagination}
        self.error = error
        self.path = path
        self.status = status.HTTP_200_OK
        return JSONResponse(status_code=status_code, content=jsonable_encoder(self))

    def error(
            self, 
            client_message_id=None, 
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            data=None, 
            error=None, 
            path=None, 
            soa_error_code=None, 
            soa_error_desc=None
        ):
        
        self.client_message_id = client_message_id
        self.data = data
        self.error = error
        self.path = path
        self.status = status_code
        self.soa_error_code = soa_error_code
        self.soa_error_desc = soa_error_desc
        return JSONResponse(status_code=status_code, content=jsonable_encoder(self))