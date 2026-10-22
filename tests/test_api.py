from fastapi.testclient import TestClient
import pytest
from src.app import app

client = TestClient(app)

def test_extract_valid_entities():
    payload = {
        "title": "Maybank announces quarterly results",
        "body": "Malayan Banking Bhd recorded strong growth in Kuala Lumpur on Monday."
    }
    response = client.post("/extract-entities", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "entities" in data
    assert "meta" in data
    assert data["meta"]["entity_count"] > 0
    assert any(ent["label"] in ["ORG", "GPE", "DATE"] for ent in data["entities"])

def test_reject_empty_title_or_body():
    payload = {
        "title": "   ",
        "body": "Valid body text here."
    }
    response = client.post("/extract-entities", json=payload)
    assert response.status_code == 400

def test_article_with_no_entities():
    payload = {
        "title": "General market overview and liquidity conditions",
        "body": "Operating margins showed stable recovery across institutional lenders during third quarter evaluations."
    }
    response = client.post("/extract-entities", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["entities"], list)

def test_repeated_entities_and_offsets():
    payload = {
        "title": "CIMB Group expands operations",
        "body": "CIMB Group opened new branches in regional markets."
    }
    response = client.post("/extract-entities", json=payload)
    assert response.status_code == 200
    data = response.json()
    offsets = [(e["start"], e["end"]) for e in data["entities"]]
    assert len(offsets) == len(set(offsets))

def test_payload_exceeding_max_limit():
    payload = {
        "title": "Standard Title",
        "body": "A" * 15000
    }
    response = client.post("/extract-entities", json=payload)
    assert response.status_code == 400
