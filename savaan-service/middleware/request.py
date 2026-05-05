from contextvars import ContextVar
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import uuid

request_id_ctx_var: ContextVar[str]= ContextVar("request_id",default="-")

def get_request_id()->str:
    return request_id_ctx_var.get()

class RequestIdMiddleWare(BaseHTTPMiddleware):
    async def dispatch(self,request:Request,call_next):
        request_id=str(uuid.uuid4())
        request_id_ctx_var.set(request_id)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response