from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.application.workflow_engine import WorkflowEngine
from app.domain.models import WorkflowDefinition, WorkflowNodeRole, WorkflowTransition, WorkflowRoleAssignment, Profile
from app.infrastructure.database import get_db
from app.schemas.workflow import (
    WorkflowDefinitionResponse,
    WorkflowTransitionResult,
    WorkflowTransitionValidateRequest,
)

router = APIRouter()


@router.get("/definitions")
async def list_workflows(db: AsyncSession = Depends(get_db)):
    """Devuelve la lista general de flujos de trabajo."""
    result = await db.execute(
        select(WorkflowDefinition).order_by(WorkflowDefinition.version.desc())
    )
    workflows = result.scalars().all()
    return {
        "data": [
            {
                "id": str(w.id),
                "name": w.name,
                "version": w.version,
                "status": w.status,
                "description": w.description,
                "created_at": w.created_at.isoformat() if w.created_at else None,
                "updated_at": w.updated_at.isoformat() if w.updated_at else None,
                "published_at": w.published_at.isoformat() if w.published_at else None,
                "total_nodes": len(w.graph_json.get("nodes", [])) if w.graph_json else 0,
                "total_edges": len(w.graph_json.get("edges", [])) if w.graph_json else 0,
            }
            for w in workflows
        ]
    }


@router.get("/active")
async def get_active_workflow(db: AsyncSession = Depends(get_db)):
    """Devuelve el flujo de trabajo activo (published) con sus roles y transiciones."""
    result = await db.execute(
        select(WorkflowDefinition).where(WorkflowDefinition.status == "published")
    )
    workflow = result.scalar_one_or_none()
    if not workflow:
        # Fallback al flujo con versión más alta
        latest = await db.execute(
            select(WorkflowDefinition).order_by(WorkflowDefinition.version.desc()).limit(1)
        )
        workflow = latest.scalar_one_or_none()
        if not workflow:
            raise HTTPException(status_code=404, detail="No existe un flujo de trabajo activo publicado.")

    # Cargar roles y transiciones asociados
    roles_res = await db.execute(
        select(WorkflowNodeRole).where(WorkflowNodeRole.workflow_id == workflow.id)
    )
    trans_res = await db.execute(
        select(WorkflowTransition).where(WorkflowTransition.workflow_id == workflow.id)
    )

    roles_list = [
        {
            "node_id": r.node_id,
            "role_name": r.role_name,
            "can_edit": r.can_edit,
            "can_approve": r.can_approve,
            "can_reject": r.can_reject,
            "required_fields": r.required_fields,
        }
        for r in roles_res.scalars().all()
    ]
    trans_list = [
        {
            "edge_id": t.edge_id,
            "label": t.label,
            "source_node_id": t.source_node_id,
            "target_node_id": t.target_node_id,
            "condition_type": t.condition_type,
            "condition_config": t.condition_config,
        }
        for t in trans_res.scalars().all()
    ]

    wf_dict = {
        "id": str(workflow.id),
        "name": workflow.name,
        "version": workflow.version,
        "status": workflow.status,
        "graph_json": workflow.graph_json,
        "description": workflow.description,
        "workflow_node_roles": roles_list,
        "workflow_transitions": trans_list,
    }

    return {
        "data": wf_dict,
        **wf_dict,
    }


@router.get("/definitions/{id}")
async def get_workflow_by_id(id: str, db: AsyncSession = Depends(get_db)):
    try:
        wf_uuid = UUID(id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID de flujo inválido")

    result = await db.execute(select(WorkflowDefinition).where(WorkflowDefinition.id == wf_uuid))
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail="Flujo no encontrado")

    roles_res = await db.execute(
        select(WorkflowNodeRole).where(WorkflowNodeRole.workflow_id == workflow.id)
    )
    trans_res = await db.execute(
        select(WorkflowTransition).where(WorkflowTransition.workflow_id == workflow.id)
    )

    return {
        "data": {
            "id": str(workflow.id),
            "name": workflow.name,
            "version": workflow.version,
            "status": workflow.status,
            "graph_json": workflow.graph_json,
            "description": workflow.description,
            "created_at": workflow.created_at.isoformat() if workflow.created_at else None,
            "updated_at": workflow.updated_at.isoformat() if workflow.updated_at else None,
            "published_at": workflow.published_at.isoformat() if workflow.published_at else None,
            "workflow_node_roles": [
                {
                    "node_id": r.node_id,
                    "role_name": r.role_name,
                    "can_edit": r.can_edit,
                    "can_approve": r.can_approve,
                    "can_reject": r.can_reject,
                    "required_fields": r.required_fields,
                }
                for r in roles_res.scalars().all()
            ],
            "workflow_transitions": [
                {
                    "edge_id": t.edge_id,
                    "label": t.label,
                    "source_node_id": t.source_node_id,
                    "target_node_id": t.target_node_id,
                    "condition_type": t.condition_type,
                    "condition_config": t.condition_config,
                }
                for t in trans_res.scalars().all()
            ],
        }
    }


@router.post("/definitions")
async def create_workflow(payload: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    clone_from_id = payload.get("clone_from")
    name = payload.get("name", "Nuevo Flujo de Trabajo")
    description = payload.get("description", "")

    max_v_res = await db.execute(select(WorkflowDefinition.version).order_by(WorkflowDefinition.version.desc()).limit(1))
    max_v = max_v_res.scalar_one_or_none() or 1
    new_version = max_v + 1

    graph_json = {"nodes": [], "edges": []}
    node_roles = []
    transitions = []

    if clone_from_id:
        try:
            from_uuid = UUID(clone_from_id)
            orig_res = await db.execute(select(WorkflowDefinition).where(WorkflowDefinition.id == from_uuid))
            orig_wf = orig_res.scalar_one_or_none()
            if orig_wf:
                graph_json = orig_wf.graph_json
                orig_roles = await db.execute(select(WorkflowNodeRole).where(WorkflowNodeRole.workflow_id == from_uuid))
                node_roles = orig_roles.scalars().all()
                orig_trans = await db.execute(select(WorkflowTransition).where(WorkflowTransition.workflow_id == from_uuid))
                transitions = orig_trans.scalars().all()
        except Exception:
            pass

    new_wf = WorkflowDefinition(
        name=name,
        version=new_version,
        status="draft",
        description=description,
        graph_json=graph_json,
    )
    db.add(new_wf)
    await db.commit()
    await db.refresh(new_wf)

    for r in node_roles:
        db.add(WorkflowNodeRole(
            workflow_id=new_wf.id,
            node_id=r.node_id,
            role_name=r.role_name,
            can_edit=r.can_edit,
            can_approve=r.can_approve,
            can_reject=r.can_reject,
            required_fields=r.required_fields,
        ))
    for t in transitions:
        db.add(WorkflowTransition(
            workflow_id=new_wf.id,
            edge_id=t.edge_id,
            label=t.label,
            source_node_id=t.source_node_id,
            target_node_id=t.target_node_id,
            condition_type=t.condition_type,
            condition_config=t.condition_config,
        ))
    await db.commit()

    return {
        "data": {
            "id": str(new_wf.id),
            "name": new_wf.name,
            "version": new_wf.version,
            "status": new_wf.status,
            "graph_json": new_wf.graph_json,
            "description": new_wf.description,
        }
    }


@router.patch("/definitions/{id}")
async def update_workflow(id: str, payload: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    try:
        wf_uuid = UUID(id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID inválido")

    result = await db.execute(select(WorkflowDefinition).where(WorkflowDefinition.id == wf_uuid))
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail="Flujo no encontrado")

    if "name" in payload:
        workflow.name = payload["name"]
    if "description" in payload:
        workflow.description = payload["description"]
    if "graph_json" in payload:
        workflow.graph_json = payload["graph_json"]
    workflow.updated_at = datetime.now(timezone.utc)

    if "node_roles" in payload and isinstance(payload["node_roles"], list):
        await db.execute(delete(WorkflowNodeRole).where(WorkflowNodeRole.workflow_id == wf_uuid))
        for r in payload["node_roles"]:
            db.add(WorkflowNodeRole(
                workflow_id=wf_uuid,
                node_id=r.get("node_id", ""),
                role_name=r.get("role_name", ""),
                can_edit=bool(r.get("can_edit", False)),
                can_approve=bool(r.get("can_approve", False)),
                can_reject=bool(r.get("can_reject", False)),
                required_fields=r.get("required_fields", []),
            ))

    if "transitions" in payload and isinstance(payload["transitions"], list):
        await db.execute(delete(WorkflowTransition).where(WorkflowTransition.workflow_id == wf_uuid))
        for t in payload["transitions"]:
            db.add(WorkflowTransition(
                workflow_id=wf_uuid,
                edge_id=t.get("edge_id", ""),
                label=t.get("label", ""),
                source_node_id=t.get("source_node_id", ""),
                target_node_id=t.get("target_node_id", ""),
                condition_type=t.get("condition_type", "always"),
                condition_config=t.get("condition_config", {}),
            ))
    elif "graph_json" in payload and isinstance(payload["graph_json"], dict):
        edges = payload["graph_json"].get("edges", [])
        if isinstance(edges, list):
            await db.execute(delete(WorkflowTransition).where(WorkflowTransition.workflow_id == wf_uuid))
            for e in edges:
                e_data = e.get("data", {})
                db.add(WorkflowTransition(
                    workflow_id=wf_uuid,
                    edge_id=e.get("id", ""),
                    label=e.get("label") or e_data.get("label", "Avanzar"),
                    source_node_id=e.get("source", ""),
                    target_node_id=e.get("target", ""),
                    condition_type=e_data.get("condition_type", "always"),
                    condition_config={
                        "allowed_roles": e_data.get("allowed_roles", []),
                        "style_config": e_data.get("style_config", {}),
                        "source_handle": e.get("sourceHandle"),
                        "target_handle": e.get("targetHandle"),
                    },
                ))

    await db.commit()
    await db.refresh(workflow)


    return {
        "data": {
            "id": str(workflow.id),
            "name": workflow.name,
            "version": workflow.version,
            "status": workflow.status,
            "graph_json": workflow.graph_json,
            "description": workflow.description,
            "updated_at": workflow.updated_at.isoformat() if workflow.updated_at else None,
        }
    }


@router.post("/definitions/{id}/publish")
async def publish_workflow(id: str, payload: Dict[str, Any] = {}, db: AsyncSession = Depends(get_db)):
    try:
        wf_uuid = UUID(id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID inválido")

    result = await db.execute(select(WorkflowDefinition).where(WorkflowDefinition.id == wf_uuid))
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail="Flujo no encontrado")

    # Archivar flujos previamente publicados
    await db.execute(
        update(WorkflowDefinition)
        .where(WorkflowDefinition.status == "published")
        .values(status="archived", updated_at=datetime.now(timezone.utc))
    )

    # Publicar flujo actual
    workflow.status = "published"
    workflow.published_at = datetime.now(timezone.utc)
    workflow.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(workflow)

    return {
        "data": {
            "id": str(workflow.id),
            "name": workflow.name,
            "version": workflow.version,
            "status": workflow.status,
            "published_at": workflow.published_at.isoformat() if workflow.published_at else None,
        }
    }


@router.get("/definitions/{id}/role-assignments")
async def get_role_assignments(id: str, db: AsyncSession = Depends(get_db)):
    try:
        wf_uuid = UUID(id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID inválido")

    result = await db.execute(
        select(WorkflowRoleAssignment, Profile)
        .join(Profile, WorkflowRoleAssignment.user_id == Profile.id)
        .where(WorkflowRoleAssignment.workflow_id == wf_uuid)
    )
    rows = result.all()
    return {
        "data": [
            {
                "id": str(ra.id),
                "workflow_id": str(ra.workflow_id),
                "user_id": str(ra.user_id),
                "role_name": ra.role_name,
                "user_name": p.name,
                "user_email": p.email,
                "created_at": ra.created_at.isoformat() if ra.created_at else None,
            }
            for ra, p in rows
        ]
    }


@router.post("/definitions/{id}/role-assignments")
async def add_role_assignment(id: str, payload: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    try:
        wf_uuid = UUID(id)
        u_uuid = UUID(payload["user_id"])
    except (ValueError, KeyError):
        raise HTTPException(status_code=400, detail="Datos de asignación inválidos")

    ra = WorkflowRoleAssignment(
        workflow_id=wf_uuid,
        user_id=u_uuid,
        role_name=payload.get("role_name", ""),
    )
    db.add(ra)
    await db.commit()
    await db.refresh(ra)
    return {"data": {"id": str(ra.id), "status": "assigned"}}


@router.delete("/definitions/{id}/role-assignments/{assignment_id}")
async def delete_role_assignment(id: str, assignment_id: str, db: AsyncSession = Depends(get_db)):
    try:
        a_uuid = UUID(assignment_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID inválido")

    await db.execute(delete(WorkflowRoleAssignment).where(WorkflowRoleAssignment.id == a_uuid))
    await db.commit()
    return {"data": {"status": "deleted"}}


@router.get("/validate-transition", response_model=WorkflowTransitionResult)
async def validate_transition(
    currentNodeId: Optional[str] = Query(None),
    targetNodeId: Optional[str] = Query(None),
    gatewayNodeId: Optional[str] = Query(None),
    userRole: str = Query(""),
    transitionLabel: str = Query(""),
    isFreeJump: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    """Evalúa si una transición es permitida bajo el motor de workflows."""
    active_wf = await get_active_workflow(db)
    return WorkflowEngine.validate_transition(
        workflow=active_wf,
        current_node_id=currentNodeId,
        target_node_id=targetNodeId,
        gateway_node_id=gatewayNodeId,
        user_role=userRole,
        form_data={},
        transition_label=transitionLabel,
        is_free_jump=isFreeJump,
    )
