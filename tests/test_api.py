from pathlib import Path

from fastapi.testclient import TestClient

from dust.api.app import app

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_formalize_full_pipeline_with_mock_provider():
    text = Path("sample_requirements.txt").read_text(encoding="utf-8")
    resp = client.post("/formalize", json={"text": text, "provider": "mock"})
    assert resp.status_code == 200
    data = resp.json()

    assert data["statements"] == 7
    assert data["ir"] is not None
    assert len(data["ir"]["requirements"]) == 7

    # EARS
    assert len(data["ears"]) == 7
    assert all("shall" in row["text"] for row in data["ears"])

    # SysML v2
    assert data["sysml"].startswith("package RequirementsModel {")
    assert "requirement def" in data["sysml"]

    # Ontology
    assert data["ontology"]["mermaid"].startswith("graph LR")
    assert data["ontology"]["graph"]["nodes"]


def test_formalize_target_subset():
    resp = client.post(
        "/formalize",
        json={"text": "The aircraft shall fly.", "provider": "mock", "targets": ["ears"]},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["ears"] is not None
    assert data["ir"] is None
    assert data["sysml"] is None
    assert data["ontology"] is None


def test_empty_text_rejected():
    resp = client.post("/formalize", json={"text": "   ", "provider": "mock"})
    assert resp.status_code == 422
