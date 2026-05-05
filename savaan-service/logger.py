import logging
from middleware.request import get_request_id

LOG_FORMAT = "[%(asctime)s] [%(levelname)s] [%(request_id)s] %(message)s"

class RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = get_request_id()
        return True
    
logger = logging.getLogger("app")
logger.setLevel(logging.INFO)

# File handler
file_handler = logging.FileHandler("savaan-service/logs/app.log")
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
file_handler.addFilter(RequestIdFilter())

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
console_handler.addFilter(RequestIdFilter())

# Attach handlers
logger.addHandler(file_handler)
logger.addHandler(console_handler)