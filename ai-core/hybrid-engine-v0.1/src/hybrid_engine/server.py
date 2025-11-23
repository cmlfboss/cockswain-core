import os
import uvicorn
from dotenv import load_dotenv
from .routes import app

def run():
    load_dotenv()
    host = os.getenv("HE_HOST", "127.0.0.1")
    port = int(os.getenv("HE_PORT", "7790"))
    log_level = os.getenv("HE_LOG_LEVEL","info")
    uvicorn.run(app, host=host, port=port, log_level=log_level)