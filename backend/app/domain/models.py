from datetime import datetime
from uuid import uuid4
from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.infrastructure.database import Base


# ------------------------------------------------------------------------------
# 1. Estructura Organizacional
# ------------------------------------------------------------------------------
class VP(Base):
    __tablename__ = "vps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(Text, unique=True, nullable=False)
    bp_name = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    direcciones = relationship("Direccion", back_populates="vp", cascade="all, delete-orphan")


class Direccion(Base):
    __tablename__ = "direcciones"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(Text, nullable=False)
    vp_id = Column(UUID(as_uuid=True), ForeignKey("vps.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    vp = relationship("VP", back_populates="direcciones")
    __table_args__ = (UniqueConstraint("name", "vp_id", name="uq_direccion_vp"),)


# ------------------------------------------------------------------------------
# 2. Usuarios y Perfiles
# ------------------------------------------------------------------------------
class Profile(Base):
    __tablename__ = "profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(Text, unique=True, nullable=False)
    name = Column(Text, nullable=False)
    vp_id = Column(UUID(as_uuid=True), ForeignKey("vps.id", ondelete="SET NULL"), nullable=True)
    direccion_id = Column(UUID(as_uuid=True), ForeignKey("direcciones.id", ondelete="SET NULL"), nullable=True)
    avatar_url = Column(Text, nullable=True)
    password_hash = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    roles = relationship("ProfileRole", back_populates="profile", cascade="all, delete-orphan")


class ProfileRole(Base):
    __tablename__ = "profile_roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    profile_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    role = Column(Text, nullable=False)
    vp_id = Column(UUID(as_uuid=True), ForeignKey("vps.id", ondelete="CASCADE"), nullable=True)
    direcciones_ids = Column(ARRAY(UUID(as_uuid=True)), default=[])
    is_transversal = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    profile = relationship("Profile", back_populates="roles")


class AppRole(Base):
    __tablename__ = "app_roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    code = Column(Text, unique=True, nullable=False)
    name = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    color = Column(Text, default="indigo")
    is_system = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class AllowedUser(Base):
    __tablename__ = "allowed_users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(Text, unique=True, nullable=False)
    name = Column(Text, nullable=False)
    password_hash = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user_roles_whitelist = relationship("UserRoleWhitelist", back_populates="user", cascade="all, delete-orphan")


class UserRoleWhitelist(Base):
    __tablename__ = "user_roles_whitelist"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    allowed_user_id = Column(UUID(as_uuid=True), ForeignKey("allowed_users.id", ondelete="CASCADE"), nullable=False)
    role = Column(Text, nullable=False)
    vp_id = Column(UUID(as_uuid=True), ForeignKey("vps.id", ondelete="SET NULL"), nullable=True)
    direcciones_ids = Column(ARRAY(UUID(as_uuid=True)), default=list)
    is_transversal = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("AllowedUser", back_populates="user_roles_whitelist")
    vp = relationship("VP")



# ------------------------------------------------------------------------------
# 3. Iniciativas
# ------------------------------------------------------------------------------
class Initiative(Base):
    __tablename__ = "initiatives"

    id = Column(String, primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    status = Column(Text, nullable=False, default="Borrador")
    form_data = Column(JSONB, nullable=False, default=dict)
    chat_history = Column(JSONB, nullable=False, default=list)
    summary = Column(JSONB, nullable=True, default=dict)
    rejection_reason = Column(Text, nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="SET NULL"), nullable=True)
    confirmed_fields = Column(JSONB, nullable=True, default=dict)
    unstructured_text = Column(Text, nullable=True)
    workflow_version = Column(Text, nullable=True)
    current_node_id = Column(Text, nullable=True)

    stage_records = relationship("InitiativeStageRecord", back_populates="initiative", cascade="all, delete-orphan")


class InitiativeField(Base):
    __tablename__ = "initiative_fields"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    label = Column(Text, nullable=False)
    key = Column(Text, unique=True, nullable=False)
    field_type = Column(Text, nullable=False)
    options = Column(JSONB, default=list)
    is_visible = Column(Boolean, default=True)
    is_required = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)
    section = Column(Text, default="form")
    depends_on = Column(Text, nullable=True)
    options_map = Column(JSONB, default=dict)
    ai_instructions = Column(Text, nullable=True)
    allow_multiple = Column(Boolean, default=False)
    help_text = Column(Text, nullable=True)
    requires_confirmation = Column(Boolean, default=False)
    ask_in_initial_form = Column(Boolean, default=False)
    file_options = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# ------------------------------------------------------------------------------
# 4. Motor de Flujos (Workflows)
# ------------------------------------------------------------------------------
class WorkflowDefinition(Base):
    __tablename__ = "workflow_definitions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(Text, nullable=False)
    version = Column(Integer, nullable=False, default=1)
    status = Column(Text, nullable=False, default="draft")
    graph_json = Column(JSONB, nullable=False, default=lambda: {"nodes": [], "edges": []})
    description = Column(Text, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    published_at = Column(DateTime(timezone=True), nullable=True)

    node_roles = relationship("WorkflowNodeRole", back_populates="workflow", cascade="all, delete-orphan")
    transitions = relationship("WorkflowTransition", back_populates="workflow", cascade="all, delete-orphan")


class WorkflowNodeRole(Base):
    __tablename__ = "workflow_node_roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflow_definitions.id", ondelete="CASCADE"), nullable=False)
    node_id = Column(Text, nullable=False)
    role_name = Column(Text, nullable=False)
    can_edit = Column(Boolean, default=False)
    can_approve = Column(Boolean, default=False)
    can_reject = Column(Boolean, default=False)
    required_fields = Column(JSONB, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    workflow = relationship("WorkflowDefinition", back_populates="node_roles")


class WorkflowTransition(Base):
    __tablename__ = "workflow_transitions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflow_definitions.id", ondelete="CASCADE"), nullable=False)
    edge_id = Column(Text, nullable=False)
    label = Column(Text, nullable=False)
    source_node_id = Column(Text, nullable=False)
    target_node_id = Column(Text, nullable=False)
    condition_type = Column(Text, nullable=False, default="always")
    condition_config = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    workflow = relationship("WorkflowDefinition", back_populates="transitions")


class WorkflowRoleAssignment(Base):
    __tablename__ = "workflow_role_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflow_definitions.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    role_name = Column(Text, nullable=False)
    assigned_by = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ------------------------------------------------------------------------------
# 5. Formularios de Etapa y Consentimientos
# ------------------------------------------------------------------------------
class StageForm(Base):
    __tablename__ = "stage_forms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    code = Column(Text, unique=True, nullable=False)
    name = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    fields = Column(JSONB, default=list)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class StageConsent(Base):
    __tablename__ = "stage_consents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    code = Column(Text, unique=True, nullable=False)
    title = Column(Text, nullable=False)
    statement = Column(Text, nullable=False)
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class DocumentTemplate(Base):
    __tablename__ = "document_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    code = Column(Text, unique=True, nullable=False)
    name = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    template_html = Column(Text, nullable=False)
    margins = Column(JSONB, default=lambda: {"top": 20, "right": 20, "bottom": 20, "left": 20})
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class InitiativeStageRecord(Base):
    __tablename__ = "initiative_stage_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    initiative_id = Column(String, ForeignKey("initiatives.id", ondelete="CASCADE"), nullable=False)
    node_id = Column(Text, nullable=False)
    stage_name = Column(Text, nullable=True)
    form_id = Column(UUID(as_uuid=True), ForeignKey("stage_forms.id", ondelete="SET NULL"), nullable=True)
    consent_id = Column(UUID(as_uuid=True), ForeignKey("stage_consents.id", ondelete="SET NULL"), nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="SET NULL"), nullable=True)
    user_name = Column(Text, nullable=True)
    user_role = Column(Text, nullable=True)
    form_data = Column(JSONB, default=dict)
    consent_accepted = Column(Boolean, default=True)
    consent_text_snapshot = Column(Text, nullable=True)
    action_taken = Column(Text, default="approved")
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())

    initiative = relationship("Initiative", back_populates="stage_records")


# ------------------------------------------------------------------------------
# 6. Base de Conocimiento y Entrenamiento de IA
# ------------------------------------------------------------------------------
class AIKnowledgeFolder(Base):
    __tablename__ = "ai_knowledge_folders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(Text, nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("ai_knowledge_folders.id", ondelete="CASCADE"), nullable=True)
    level = Column(Integer, default=1)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class AITrainingConfig(Base):
    __tablename__ = "ai_training_config"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    layer = Column(Text, nullable=False)
    title = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    source = Column(Text, default="manual")
    folder_id = Column(UUID(as_uuid=True), ForeignKey("ai_knowledge_folders.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# ------------------------------------------------------------------------------
# 7. Logs de Agentes, Correos y Configuración del Sistema
# ------------------------------------------------------------------------------
class AgentLog(Base):
    __tablename__ = "agent_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    agent_name = Column(Text, nullable=True)
    action = Column(Text, nullable=True)
    agent_role = Column(Text, nullable=True)
    task_title = Column(Text, nullable=True)
    status = Column(Text, nullable=False, default="completed")
    progress = Column(Integer, default=100)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class EmailLog(Base):
    __tablename__ = "email_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    initiative_id = Column(Text, nullable=True)
    recipient = Column(Text, nullable=False)
    subject = Column(Text, nullable=False)
    body = Column(Text, nullable=False)
    status = Column(Text, nullable=False, default="sent")
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class SiteSetting(Base):
    __tablename__ = "site_settings"

    id = Column(Integer, primary_key=True, default=1)
    maintenance_mode = Column(Boolean, default=False, nullable=False)
    system_notice = Column(Text, nullable=True)
    sandbox_enabled = Column(Boolean, default=True, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class AIFeedback(Base):
    __tablename__ = "ai_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    initiative_id = Column(Text, nullable=True)
    message_index = Column(Integer, default=0)
    user_message = Column(Text, nullable=False)
    agent_response = Column(Text, nullable=False)
    rating = Column(Text, nullable=False)
    admin_approved = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

