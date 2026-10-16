import pytest
from app.core.security import create_access_token
from app.domain.models import Initiative
from app.api.v1.endpoints.initiatives import is_initiative_draft, is_user_initiative_registrador

def test_is_initiative_draft():
    # Iniciativa en Borrador
    init_borrador = Initiative(id="test-1", status="Borrador", current_node_id="borrador")
    assert is_initiative_draft(init_borrador) is True

    init_borrador_2 = Initiative(id="test-2", status="1. Borrador", current_node_id="node_borrador")
    assert is_initiative_draft(init_borrador_2) is True

    init_chat = Initiative(id="test-3", status="Chat", current_node_id="borrador")
    assert is_initiative_draft(init_chat) is True

    # Iniciativas en siguientes estados
    init_pendiente = Initiative(id="test-4", status="Pendiente de aprobación", current_node_id="eval_bp")
    assert is_initiative_draft(init_pendiente) is False

    init_observada = Initiative(id="test-5", status="Observada", current_node_id="observada")
    assert is_initiative_draft(init_observada) is False

    init_demanda = Initiative(id="test-6", status="En demanda", current_node_id="planificacion")
    assert is_initiative_draft(init_demanda) is False

    init_planificada = Initiative(id="test-7", status="Iniciativa planificada", current_node_id="planificacion")
    assert is_initiative_draft(init_planificada) is False

    init_desestimada = Initiative(id="test-8", status="Desestimada", current_node_id="desestimada")
    assert is_initiative_draft(init_desestimada) is False


def test_is_user_initiative_registrador():
    claims_user_a = {
        "sub": "11111111-1111-1111-1111-111111111111",
        "email": "usera@empresa.com",
        "name": "Usuario Registrador A",
        "roles": ["registrador"],
    }
    claims_user_b = {
        "sub": "22222222-2222-2222-2222-222222222222",
        "email": "userb@empresa.com",
        "name": "Usuario Registrador B",
        "roles": ["registrador"],
    }

    init_of_a = Initiative(
        id="init-a",
        status="Borrador",
        form_data={
            "registrador": "Usuario Registrador A",
            "registrador_email": "usera@empresa.com",
        }
    )

    # Usuario A es el registrador
    assert is_user_initiative_registrador(init_of_a, claims_user_a) is True

    # Usuario B NO es el registrador
    assert is_user_initiative_registrador(init_of_a, claims_user_b) is False


@pytest.mark.asyncio
async def test_e2e_draft_privacy_lifecycle():
    import httpx
    BASE_URL = "http://127.0.0.1:8000"

    try:
        r = httpx.get(f"{BASE_URL}/api/health", timeout=1.0)
        if r.status_code != 200:
            pytest.skip("Backend no disponible")
    except Exception:
        pytest.skip("Backend no disponible")

    token_user_a = create_access_token({
        "sub": "a0000000-0000-0000-0000-000000000001",
        "email": "ana.registradora@empresa.com",
        "name": "Ana Registradora",
        "roles": ["registrador"],
    })
    token_user_b = create_access_token({
        "sub": "b0000000-0000-0000-0000-000000000002",
        "email": "bernardo.otro@empresa.com",
        "name": "Bernardo Otro",
        "roles": ["registrador", "bp_ti"],
    })

    headers_a = {"Authorization": f"Bearer {token_user_a}"}
    headers_b = {"Authorization": f"Bearer {token_user_b}"}

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        # 1. Ana crea un borrador
        draft_payload = {
            "status": "Borrador",
            "current_node_id": "borrador",
            "form_data": {
                "titulo": "Iniciativa Privada de Ana",
                "institucion": "UPC",
                "vicepresidencia": "Comercial",
                "registrador": "Ana Registradora",
                "registrador_email": "ana.registradora@empresa.com",
            },
            "summary": {"titulo": "Iniciativa Privada de Ana"},
            "chat_history": [],
        }
        res_create = await client.post("/api/v1/initiatives", json=draft_payload, headers=headers_a)
        assert res_create.status_code == 200
        created = res_create.json()
        init_id = created["id"]

        # 2. Ana puede listar y ver su propio borrador
        res_list_a = await client.get("/api/v1/initiatives", headers=headers_a)
        assert res_list_a.status_code == 200
        list_a = res_list_a.json()
        assert any(i["id"] == init_id for i in list_a)

        res_detail_a = await client.get(f"/api/v1/initiatives/{init_id}", headers=headers_a)
        assert res_detail_a.status_code == 200

        # 3. Bernardo NO puede ver el borrador de Ana en la lista general
        res_list_b = await client.get("/api/v1/initiatives", headers=headers_b)
        assert res_list_b.status_code == 200
        list_b = res_list_b.json()
        assert not any(i["id"] == init_id for i in list_b)

        # 4. Bernardo intenta acceder por ID directo al borrador de Ana -> 403 Forbidden
        res_detail_b = await client.get(f"/api/v1/initiatives/{init_id}", headers=headers_b)
        assert res_detail_b.status_code == 403
        assert "borrador solo las puede visualizar el registrador" in res_detail_b.json().get("detail", "")

        # 5. Bernardo intenta modificar el borrador de Ana -> 403 Forbidden
        res_patch_b = await client.patch(
            f"/api/v1/initiatives/{init_id}",
            json={"status": "Observada"},
            headers=headers_b
        )
        assert res_patch_b.status_code == 403

        # 6. Ana pasa la iniciativa a un SIGUIENTE ESTADO (Pendiente de aprobación)
        res_advance = await client.patch(
            f"/api/v1/initiatives/{init_id}",
            json={
                "status": "Pendiente de aprobación",
                "current_node_id": "eval_bp",
            },
            headers=headers_a
        )
        assert res_advance.status_code == 200

        # 7. Ahora que pasó al siguiente estado, RECIÉN se hace visible para Bernardo
        res_detail_b_after = await client.get(f"/api/v1/initiatives/{init_id}", headers=headers_b)
        assert res_detail_b_after.status_code == 200
        assert res_detail_b_after.json()["status"] == "Pendiente de aprobación"

        res_list_b_after = await client.get("/api/v1/initiatives", headers=headers_b)
        assert res_list_b_after.status_code == 200
        assert any(i["id"] == init_id for i in res_list_b_after.json())
