
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class ChatMessage(BaseModel):
    role: str = Field(..., description="user|assistant|system")
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    metadata: Optional[Dict[str, Any]] = None

class ProxyResponse(BaseModel):
    status: int
    body: str
    upstream: str
    request_id: str
