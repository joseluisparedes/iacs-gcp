import logging
from typing import Any, Dict, List, Optional, Set
from app.schemas.workflow import WorkflowTransitionResult

logger = logging.getLogger(__name__)

ROLE_ALIASES: Dict[str, List[str]] = {
    "vicepresidente": ["vicepresidente", "vicepresidente_del_negocio", "vp"],
    "vicepresidente_del_negocio": ["vicepresidente", "vicepresidente_del_negocio", "vp"],
    "gestor_demanda": ["gestor_demanda", "gestor_de_la_demanda"],
    "gestor_de_la_demanda": ["gestor_demanda", "gestor_de_la_demanda"],
    "lider_dominio": ["lider_dominio", "lider_de_dominio"],
    "lider_de_dominio": ["lider_dominio", "lider_de_dominio"],
    "business_owner": ["business_owner", "bo"],
    "registrador": ["registrador", "key_user"],
    "admin": ["admin", "administrador", "administrador_general"],
}


def expand_user_roles(raw_roles: str) -> Set[str]:
    """Expande la lista de roles del usuario según los alias configurados."""
    roles_list = [r.strip().lower() for r in raw_roles.split(",") if r.strip()]
    expanded: Set[str] = set()
    for role in roles_list:
        expanded.add(role)
        if role in ROLE_ALIASES:
            expanded.update(ROLE_ALIASES[role])
    return expanded


def evaluate_gateway_condition(
    gateway_node: Dict[str, Any],
    form_data: Dict[str, Any],
    edge: Dict[str, Any],
) -> bool:
    """Evalúa si una arista que sale de una compuerta cumple con su condición lógica."""
    config = gateway_node.get("data", {}).get("gatewayConfig", {})
    var_name = config.get("variable", "")
    rules = config.get("rules", [])

    actual_val = str(form_data.get(var_name, "")).strip().lower()

    # Buscar regla asociada a este edgeId o targetNodeId
    rule = next((r for r in rules if r.get("edgeId") == edge.get("id") or r.get("targetNodeId") == edge.get("target")), None)
    if not rule:
        return False

    if rule.get("isDefault"):
        return True

    expected_val = str(rule.get("value", "")).strip().lower()
    op = rule.get("operator", "equals")

    if op == "equals":
        return actual_val == expected_val
    elif op == "not_equals":
        return actual_val != expected_val
    elif op == "contains":
        return expected_val in actual_val
    elif op in ("greater_than", "less_than"):
        try:
            num_actual = float(actual_val)
            num_expected = float(expected_val)
            return (num_actual > num_expected) if op == "greater_than" else (num_actual < num_expected)
        except ValueError:
            return False

    return False


class WorkflowEngine:
    """
    Motor evaluador de transiciones, permisos y reglas de negocio para el flujo de iniciativas.
    Reemplaza la lógica distribuida manteniendo 100% de paridad funcional con workflowEngine.ts.
    """

    @staticmethod
    def validate_transition(
        workflow: Optional[Dict[str, Any]],
        current_node_id: Optional[str],
        target_node_id: Optional[str],
        gateway_node_id: Optional[str],
        user_role: str,
        form_data: Dict[str, Any],
        transition_label: str,
        is_free_jump: bool = False,
    ) -> WorkflowTransitionResult:
        if not workflow or not current_node_id:
            # Modo legado / permisivo si no hay flujo configurado
            return WorkflowTransitionResult(allowed=True)

        user_roles_set = expand_user_roles(user_role)
        has_admin = "admin" in user_roles_set or "administrador" in user_roles_set

        nodes = workflow.get("graph_json", {}).get("nodes", [])
        edges = workflow.get("graph_json", {}).get("edges", [])
        node_roles = workflow.get("workflow_node_roles", [])
        transitions = workflow.get("workflow_transitions", [])

        # Buscar permisos del rol en el nodo actual
        matched_node_role = next(
            (r for r in node_roles if r.get("node_id") == current_node_id and str(r.get("role_name", "")).lower() in user_roles_set),
            None
        )

        # 1. Acciones de guardado estándar (sin cambio de estado)
        if transition_label in ("Guardar", "Borrador") or (target_node_id and target_node_id == current_node_id):
            if not has_admin and matched_node_role and not matched_node_role.get("can_edit", False):
                return WorkflowTransitionResult(
                    allowed=False,
                    reason=f"Tu rol ({', '.join(user_roles_set)}) no cuenta con permiso de edición en este nodo."
                )
            return WorkflowTransitionResult(allowed=True, next_node_id=current_node_id)

        # 1b. Salto Libre / Reubicación Manual
        if transition_label == "Salto Libre" or is_free_jump:
            current_node = next((n for n in nodes if n.get("id") == current_node_id), None)
            if current_node and current_node.get("data", {}).get("allowManualStateMove"):
                allowed_role = str(current_node.get("data", {}).get("manualStateMoveRole", "")).strip().lower()
                if allowed_role and allowed_role not in user_roles_set and not has_admin:
                    return WorkflowTransitionResult(
                        allowed=False,
                        reason=f"Tu rol no está autorizado para mover manualmente la iniciativa desde este estado (requiere rol: {allowed_role})."
                    )
                return WorkflowTransitionResult(allowed=True, next_node_id=target_node_id or current_node_id)
            if has_admin:
                return WorkflowTransitionResult(allowed=True, next_node_id=target_node_id or current_node_id)
            return WorkflowTransitionResult(
                allowed=False,
                reason="El salto manual de estado no está habilitado para este estado en el flujo de trabajo."
            )

        # 2. Buscar transición directa
        transition = next(
            (t for t in transitions if t.get("source_node_id") == current_node_id and (
                (target_node_id and t.get("target_node_id") == target_node_id) or
                (transition_label and str(t.get("label", "")).lower() == transition_label.lower())
            )),
            None
        )
        if not transition:
            edge = next(
                (e for e in edges if e.get("source") == current_node_id and (
                    (target_node_id and e.get("target") == target_node_id) or
                    (transition_label and str(e.get("label", "")).lower() == transition_label.lower())
                )),
                None
            )
            if edge:
                transition = {
                    "target_node_id": edge.get("target"),
                    "label": edge.get("label", transition_label),
                    "condition_type": "always",
                    "condition_config": {}
                }

        # 2b. Buscar si el nodo conecta a una compuerta (Gateway)
        intermediate_gateway = gateway_node_id
        if not transition and not intermediate_gateway:
            gateway_edge = next(
                (e for e in edges if e.get("source") == current_node_id and any(
                    n.get("id") == e.get("target") and n.get("type") == "gateway" for n in nodes
                )),
                None
            )
            if gateway_edge:
                intermediate_gateway = gateway_edge.get("target")

        # Evaluar salida de compuerta
        if intermediate_gateway:
            gw_node = next((n for n in nodes if n.get("id") == intermediate_gateway), None)
            if gw_node:
                outgoing_edges = [e for e in edges if e.get("source") == intermediate_gateway]
                for edge in outgoing_edges:
                    if evaluate_gateway_condition(gw_node, form_data, edge):
                        transition = {
                            "target_node_id": edge.get("target"),
                            "label": edge.get("label", transition_label),
                            "condition_type": "always",
                            "condition_config": {}
                        }
                        break

        if not transition:
            return WorkflowTransitionResult(
                allowed=False,
                reason=f"No existe una transición válida desde el nodo actual con la acción '{transition_label}'."
            )

        # 2c. Validación de roles autorizados a nivel de transición (RBAC de flecha)
        trans_allowed_roles = []
        if isinstance(transition, dict):
            cond_cfg = transition.get("condition_config") or {}
            trans_allowed_roles = cond_cfg.get("allowed_roles") or transition.get("allowed_roles") or []
        if trans_allowed_roles and not has_admin:
            trans_roles_set = {r.strip().lower() for r in trans_allowed_roles if r.strip()}
            if not user_roles_set.intersection(trans_roles_set):
                return WorkflowTransitionResult(
                    allowed=False,
                    reason=f"Tu rol ({', '.join(user_roles_set)}) no está autorizado para ejecutar la acción '{transition_label}'."
                )

        # 3. Validación de permisos de Aprobación / Rechazo
        is_rejection = transition_label in ("Rechazar", "Desestimar", "Observar")
        if not has_admin and matched_node_role:
            if is_rejection and not matched_node_role.get("can_reject", False):
                return WorkflowTransitionResult(
                    allowed=False,
                    reason="El rol asignado no cuenta con permiso para rechazar u observar desde este estado."
                )
            if not is_rejection and not matched_node_role.get("can_approve", False):
                return WorkflowTransitionResult(
                    allowed=False,
                    reason="El rol asignado no cuenta con permiso para aprobar o avanzar desde este estado."
                )

        # 4. Validación de campos requeridos del nodo
        required_fields = []
        if matched_node_role and matched_node_role.get("required_fields"):
            required_fields.extend(matched_node_role.get("required_fields"))

        curr_node = next((n for n in nodes if n.get("id") == current_node_id), None)
        if curr_node and curr_node.get("data", {}).get("requiredFields"):
            required_fields.extend(curr_node.get("data", {}).get("requiredFields"))

        def is_empty(val: Any) -> bool:
            if val is None:
                return True
            if isinstance(val, (list, dict, set, tuple)):
                return len(val) == 0
            return not str(val).strip()

        missing = [f for f in set(required_fields) if is_empty(form_data.get(f))]
        if missing:
            return WorkflowTransitionResult(
                allowed=False,
                reason=f"Existen campos obligatorios pendientes de completar: {', '.join(missing)}.",
                missing_fields=missing
            )

        target_node = next((n for n in nodes if n.get("id") == transition.get("target_node_id")), None)
        next_label = target_node.get("data", {}).get("label") if target_node else transition.get("target_node_id")

        return WorkflowTransitionResult(
            allowed=True,
            next_node_id=transition.get("target_node_id"),
            next_node_label=next_label
        )
