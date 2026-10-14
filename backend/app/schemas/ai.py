from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TeoChatRequest(BaseModel):
    history: List[Dict[str, Any]] = Field(default_factory=list)
    message: str
    initialData: Optional[Dict[str, Any]] = Field(default_factory=dict)
    aiFields: Optional[List[Dict[str, Any]]] = Field(default_factory=list)


class TeoChatResponse(BaseModel):
    text: str
    options: List[str] = Field(default_factory=list)
    allow_multiple: bool = False
    extractedFields: Dict[str, Any] = Field(default_factory=dict)


class SummarizeRequest(BaseModel):
    history: List[Dict[str, Any]] = Field(default_factory=list)
    initialData: Optional[Dict[str, Any]] = Field(default_factory=dict)
    aiFields: Optional[List[Dict[str, Any]]] = Field(default_factory=list)


class SpeechToTextResponse(BaseModel):
    text: str
    confidence: Optional[float] = None
