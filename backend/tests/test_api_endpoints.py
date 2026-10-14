import httpx
import pytest

BASE_URL = "http://127.0.0.1:8000"


def is_server_reachable():
    try:
        r = httpx.get(f"{BASE_URL}/api/health", timeout=1.0)
        return r.status_code == 200
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not is_server_reachable(),
    reason="Requiere el servidor backend activo en 127.0.0.1:8000 (pruebas e2e)",
)

@pytest.mark.asyncio
async def test_initiatives_endpoint():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        response = await client.get("/api/v1/initiatives")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 11
        init1 = next((i for i in data if i.get("id") == "INIT-SAMPLE-01"), None)
        assert init1 is not None
        assert init1["form_data"]["vicepresidencia"] == "Comercial"
        assert init1["status"] == "Borrador"

@pytest.mark.asyncio
async def test_structure_endpoints():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        vp_res = await client.get("/api/v1/vps")
        assert vp_res.status_code == 200
        vps = vp_res.json()
        assert len(vps) >= 6

        dir_res = await client.get("/api/v1/direcciones")
        assert dir_res.status_code == 200
        direcciones = dir_res.json()
        assert len(direcciones) >= 19

@pytest.mark.asyncio
async def test_ai_training_endpoints():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        folders_res = await client.get("/api/v1/admin/ai-training/folders")
        assert folders_res.status_code == 200
        folders = folders_res.json()
        assert len(folders) >= 5

        entries_res = await client.get("/api/v1/admin/ai-training")
        assert entries_res.status_code == 200
        entries = entries_res.json()
        assert len(entries) >= 5

@pytest.mark.asyncio
async def test_chat_teo_endpoint():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        payload = {
            "message": "Hola Teo, quiero registrar una necesidad de automatización de admisiones.",
            "history": [],
            "initialData": {
                "institucion": "UPC",
                "vicepresidencia": "Comercial",
                "registrador": "Administrador General"
            }
        }
        res = await client.post("/api/v1/chat", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert "text" in data
        assert isinstance(data["text"], str)
        assert len(data["text"]) > 0
        assert "options" in data
