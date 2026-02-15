from pydantic import BaseModel, Field
from typing import Optional, List

class ChatRequest(BaseModel):
    user_id: str = Field(default="demo_user")
    session_id: Optional[int] = None
    message: str
    use_web: bool = True

class Source(BaseModel):
    title: str
    url: str

class ChatResponse(BaseModel):
    session_id: int
    answer: str
    verified: bool = False
    sources: List[Source] = []
    steps: List[str] = []
