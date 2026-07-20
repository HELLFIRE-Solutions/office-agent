# TETA+PI Relationship

TETA+PI is a sibling project to HELLFIRE AI Solutions — they share people,
implementation patterns, and the TWIRA (Trust-Weighted Intent Routing)
verification logic used in the compliance/trust layer module.

## Shared infrastructure

- The production server (a DigitalOcean droplet, EU region `fra1` /
  Frankfurt, satisfying DSGVO data residency) is currently shared between
  TETA+PI (already in production) and HELLFIRE. Cross-project isolation is
  maintained deliberately: HELLFIRE runs under its own deploy user
  (`hellfire`, no sudo, own Docker network `hellfire_net`) so TETA+PI's
  containers (`tetapi-redis`, `tetapi-postgres`) are never touched by
  HELLFIRE deploys.
- Firewall (ufw) and fail2ban are already active and shared across both
  projects.

## Why this matters for internal knowledge base search

Questions that mention "the server," "the droplet," or infrastructure
details may be about either project — always check which project a query
is scoped to before answering, since the shared server means infra
answers can otherwise bleed between the two.
