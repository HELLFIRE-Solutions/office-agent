# HELLFIRE AI Solutions — Business Model

HELLFIRE AI Solutions implements agentic AI infrastructure for mid-market
businesses, DACH-first then US (California, New York). The approach is
modeled loosely on Anthropic's internal "Ode" tools philosophy, but aimed
at mid-market clients rather than Fortune 500 companies.

## Dogfooding principle

Every module is first built and used for real inside HELLFIRE itself (and
its sibling project TETA+PI). Only after a module proves itself internally
does a universal template get extracted and sold to clients at a fixed
price. A module, commercially, equals template + install labor.

## Sales and delivery constraints

- Sales always go through a human. There is no self-serve signup at launch.
- Onboarding and training is a separate paid offering, not a free step
  bundled with a module purchase.
- After a module is implemented, clients choose between keeping a human on
  contract (minimum / medium / full-time tiers — never billed hourly) or
  moving to AI-only chat support.
- Every module must be demoable. Clients need to see it work, not take
  functionality on faith.

## Compliance

DSGVO / EU data residency is treated as a hard requirement: servers and
databases must be EU-hosted. This is the entry ticket to the German market
and is non-negotiable for any module that touches client data.

## Pricing shape

Contracts come in two shapes (see the `crm.contracts` schema in
internal-db):

- **Module contracts** — a fixed price for a catalog module.
- **People contracts** — a contractor retainer billed by tier (min /
  medium / full-time), never by the hour.

All contract currency defaults to EUR.
