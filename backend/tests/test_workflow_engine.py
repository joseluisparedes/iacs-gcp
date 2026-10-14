import pytest
from app.application.workflow_engine import WorkflowEngine


@pytest.fixture
def sample_workflow():
    return {
        "graph_json": {
            "nodes": [
                {
                    "id": "node_borrador",
                    "type": "state",
                    "data": {"label": "Borrador", "requiredFields": ["titulo"]}
                },
                {
                    "id": "node_pendiente",
                    "type": "state",
                    "data": {"label": "Pendiente de aprobación"}
                }
            ],
            "edges": [
                {
                    "id": "edge_1",
                    "source": "node_borrador",
                    "target": "node_pendiente",
                    "label": "Enviar a Revisión"
                }
            ]
        },
        "workflow_node_roles": [
            {
                "node_id": "node_borrador",
                "role_name": "registrador",
                "can_edit": True,
                "can_approve": True,
                "can_reject": False
            }
        ],
        "workflow_transitions": []
    }


def test_transition_allowed_with_required_fields(sample_workflow):
    result = WorkflowEngine.validate_transition(
        workflow=sample_workflow,
        current_node_id="node_borrador",
        target_node_id="node_pendiente",
        gateway_node_id=None,
        user_role="registrador",
        form_data={"titulo": "Automatización de Matrícula"},
        transition_label="Enviar a Revisión"
    )
    assert result.allowed is True
    assert result.next_node_id == "node_pendiente"


def test_transition_blocked_when_missing_required_fields(sample_workflow):
    result = WorkflowEngine.validate_transition(
        workflow=sample_workflow,
        current_node_id="node_borrador",
        target_node_id="node_pendiente",
        gateway_node_id=None,
        user_role="registrador",
        form_data={"titulo": "   "},
        transition_label="Enviar a Revisión"
    )
    assert result.allowed is False
    assert "titulo" in result.missing_fields


def test_transition_with_allowed_roles_rbac(sample_workflow):
    sample_workflow["workflow_transitions"] = [
        {
            "edge_id": "edge_1",
            "source_node_id": "node_borrador",
            "target_node_id": "node_pendiente",
            "label": "Enviar a Revisión",
            "condition_type": "role_only",
            "condition_config": {"allowed_roles": ["bp_ti", "lider_dominio"]}
        }
    ]

    # Rol no autorizado
    blocked_result = WorkflowEngine.validate_transition(
        workflow=sample_workflow,
        current_node_id="node_borrador",
        target_node_id="node_pendiente",
        gateway_node_id=None,
        user_role="registrador",
        form_data={"titulo": "Iniciativa A"},
        transition_label="Enviar a Revisión"
    )
    assert blocked_result.allowed is False
    assert "no está autorizado" in blocked_result.reason

    # Rol autorizado
    allowed_result = WorkflowEngine.validate_transition(
        workflow=sample_workflow,
        current_node_id="node_borrador",
        target_node_id="node_pendiente",
        gateway_node_id=None,
        user_role="bp_ti",
        form_data={"titulo": "Iniciativa A"},
        transition_label="Enviar a Revisión"
    )
    assert allowed_result.allowed is True
    assert allowed_result.next_node_id == "node_pendiente"

    # Admin bypass
    admin_result = WorkflowEngine.validate_transition(
        workflow=sample_workflow,
        current_node_id="node_borrador",
        target_node_id="node_pendiente",
        gateway_node_id=None,
        user_role="admin",
        form_data={"titulo": "Iniciativa A"},
        transition_label="Enviar a Revisión"
    )
    assert admin_result.allowed is True
