import json

import pytest

from office_agent.docgen.generate import DocgenError, render_contract, render_offer

CLIENT = {"legal_name": "Example Mittelstand GmbH", "country_code": "DE"}


def test_render_offer_from_sample_file():
    data = json.loads(open("samples/offer_example.json", encoding="utf-8").read())
    rendered = render_offer(data)
    assert "Example Mittelstand GmbH" in rendered
    assert "12000.00 EUR" in rendered
    assert "AI Office" in rendered


def test_render_offer_missing_field_raises():
    with pytest.raises(DocgenError):
        render_offer({"client": CLIENT})


def test_render_module_contract():
    data = {
        "client": CLIENT,
        "contract_type": "module",
        "module_name": "AI Office",
        "fixed_price": 12000.0,
        "currency": "EUR",
        "start_date": "2026-08-01",
        "status": "draft",
    }
    rendered = render_contract(data)
    assert "**Contract type:** module" in rendered
    assert "12000.00 EUR" in rendered


def test_render_people_contract():
    data = {
        "client": CLIENT,
        "contract_type": "people",
        "contractor_name": "Jane Contractor",
        "people_tier": "medium",
        "monthly_rate": 3500.0,
        "currency": "EUR",
        "start_date": "2026-08-01",
    }
    rendered = render_contract(data)
    assert "**Tier:** medium" in rendered
    assert "3500.00 EUR" in rendered


def test_render_contract_invalid_tier_raises():
    data = {
        "client": CLIENT,
        "contract_type": "people",
        "contractor_name": "Jane Contractor",
        "people_tier": "hourly",
        "monthly_rate": 3500.0,
        "currency": "EUR",
        "start_date": "2026-08-01",
    }
    with pytest.raises(DocgenError):
        render_contract(data)


def test_render_contract_unknown_type_raises():
    with pytest.raises(DocgenError):
        render_contract({"client": CLIENT, "contract_type": "hourly"})
