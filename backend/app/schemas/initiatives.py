from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str  # 'user' | 'model'
    text: str


class InitiativeBase(BaseModel):
    status: str = "Borrador"
    form_data: Dict[str, Any] = Field(default_factory=dict)
    chat_history: List[ChatMessage] = Field(default_factory=list)
    summary: Optional[Dict[str, Any]] = None
    rejection_reason: Optional[str] = None
    confirmed_fields: Optional[Dict[str, bool]] = Field(default_factory=dict)
    unstructured_text: Optional[str] = None
    workflow_version: Optional[str] = None
    current_node_id: Optional[str] = None


class InitiativeCreate(InitiativeBase):
    id: Optional[str] = None


class InitiativeUpdate(BaseModel):
    status: Optional[str] = None
    form_data: Optional[Dict[str, Any]] = None
    chat_history: Optional[List[ChatMessage]] = None
    summary: Optional[Dict[str, Any]] = None
    rejection_reason: Optional[str] = None
    confirmed_fields: Optional[Dict[str, bool]] = None
    unstructured_text: Optional[str] = None
    workflow_version: Optional[str] = None
    current_node_id: Optional[str] = None


class InitiativeResponse(InitiativeBase):
    id: str
    created_at: datetime
    updated_at: datetime
    user_id: Optional[UUID] = None

    class Config:
        from_attributes = True
