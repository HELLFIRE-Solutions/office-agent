"""Render contracts/offers from data dicts shaped like internal-db rows.

Field names deliberately mirror `crm.clients` / `crm.contracts` (see
internal-db/migrations/0002_catalog_and_clients.sql and 0004_contracts.sql)
so a future integration can pass a DB row straight through without a
translation layer. contract_type mirrors the DB's CHECK constraint: exactly
one of (module_name, fixed_price) or (contractor_name, people_tier,
monthly_rate) must be present.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined

TEMPLATES_DIR = Path(__file__).parent / "templates"

_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    undefined=StrictUndefined,
    keep_trailing_newline=True,
)

REQUIRED_CLIENT_FIELDS = {"legal_name"}
REQUIRED_MODULE_FIELDS = {"module_name", "fixed_price", "currency", "start_date"}
REQUIRED_PEOPLE_FIELDS = {"contractor_name", "people_tier", "monthly_rate", "currency", "start_date"}

# Optional fields every template references — default to None so StrictUndefined
# only ever catches genuinely missing *required* fields, not unset optional ones.
OPTIONAL_DEFAULTS = {
    "end_date": None,
    "notes": None,
    "status": None,
    "primary_contact": None,
}
CLIENT_OPTIONAL_DEFAULTS = {"display_name": None, "country_code": None}


def _with_defaults(data: dict[str, Any]) -> dict[str, Any]:
    merged = {**OPTIONAL_DEFAULTS, **data}
    merged["client"] = {**CLIENT_OPTIONAL_DEFAULTS, **data["client"]}
    return merged


class DocgenError(ValueError):
    pass


def _require(data: dict[str, Any], fields: set[str], label: str) -> None:
    missing = fields - data.keys()
    if missing:
        raise DocgenError(f"missing required {label} field(s): {sorted(missing)}")


def render_offer(data: dict[str, Any]) -> str:
    _require(data, {"client"}, "offer")
    _require(data["client"], REQUIRED_CLIENT_FIELDS, "client")
    _require(data, REQUIRED_MODULE_FIELDS, "offer")
    template = _env.get_template("offer.md.j2")
    return template.render(**_with_defaults(data))


def render_contract(data: dict[str, Any]) -> str:
    _require(data, {"client", "contract_type"}, "contract")
    _require(data["client"], REQUIRED_CLIENT_FIELDS, "client")

    contract_type = data["contract_type"]
    if contract_type == "module":
        _require(data, REQUIRED_MODULE_FIELDS, "module contract")
        template = _env.get_template("contract_module.md.j2")
    elif contract_type == "people":
        _require(data, REQUIRED_PEOPLE_FIELDS, "people contract")
        if data["people_tier"] not in {"min", "medium", "fulltime"}:
            raise DocgenError(f"people_tier must be one of min/medium/fulltime, got {data['people_tier']!r}")
        template = _env.get_template("contract_people.md.j2")
    else:
        raise DocgenError(f"contract_type must be 'module' or 'people', got {contract_type!r}")

    return template.render(**_with_defaults(data))
