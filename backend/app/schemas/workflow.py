from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class WorkflowTransitionValidateRequest(BaseModel):
    workflow_id: Optional[str] = None
    current_node_id: Optional[str] = None
    target_node_id: Optional[str] = None
    gateway_node_id: Optional[str] = None
    user_role: str
    form_data: Dict[str, Any] = Field(default_factory=dict)
    transition_label: str
    is_free_jump: Optional[bool] = False


class WorkflowTransitionResult(BaseModel):
    allowed: bool
    reason: Optional[str] = None
    missing_fields: Optional[List[str]] = None
    next_node_id: Optional[str] = None
    next_node_label: Optional[str] = None


class WorkflowDefinitionResponse(BaseModel):
    id: UUID
    name: str
    version: int
    status: str
    graph_json: Dict[str, Any]
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None

    class Config:
        from_attributes = True
