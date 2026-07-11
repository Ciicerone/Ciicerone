# Internal Brief — Ajibola Shokunbi

**Role:** Core Software Lead  
**GitHub:** @jiboo2022  
**Color Team:** Infrastructure / Yellow  
**Active Window:** Weeks 1–20  
**Status:** Critical path owner for the entire bank-pilot timeline

---

## Mission

Build the application-layer substrate that every other maintainer depends on. If Ajibola's work slips in Phase 0 or Phase 2, the entire timeline slips.

---

## Atomic Tasks

### Phase 0 — Foundation (Weeks 1–4)

| Task | Weeks | Deliverable | Unblocks |
|------|-------|-------------|----------|
| AJIBOLA-001 | 1 | Production ORM base + session factory (`db/base.py`, `db/session.py`, `db/health.py`) | All DB-backed models |
| AJIBOLA-002 | 1–2 | Wire `EventStore` into `Simulator` by default | P0-5 audit trail |
| AJIBOLA-003 | 2–3 | Shared event bus (`core/event_bus.py`) | Red/blue/purple/white/black communication |
| AJIBOLA-005 | 3–4 | Core simulation ORM models (`db/models/simulation.py`, `db/models/campaign.py`) | P0-6 persistence |

### Phase 1 — Security & Multi-Tenancy (Weeks 5–8)

| Task | Weeks | Deliverable | Unblocks |
|------|-------|-------------|----------|
| AJIBOLA-004 | 5–6 | API auth middleware + `User`/`Role`/`Tenant` models | Ibrahim's RBAC |
| AJIBOLA-006 | 7–8 | Multi-tenant isolation (`db/tenant_filter.py`, `TenantMiddleware`) | All tenant-scoped queries |

### Phase 2 — Orchestration (Weeks 9–14)

| Task | Weeks | Deliverable | Unblocks |
|------|-------|-------------|----------|
| AJIBOLA-007 | 9–11 | `ExerciseOrchestrator` — red→blue→purple→black chain | End-to-end platform |
| AJIBOLA-008 | 11–12 | Wire `Simulator` output to Blue Team via event bus | Red→blue detection loop |
| AJIBOLA-009 | 13–14 | Enterprise integrations API (`api/routers/integrations.py`) | API-managed deployments |

### Phase 4 — Pilot Validation (Weeks 19–20)

| Task | Weeks | Deliverable |
|------|-------|-------------|
| AJIBOLA-010 | 19–20 | Full end-to-end pilot dry-run and sign-off |

---

## Key Collaboration Points

- **Omolara:** Ajibola defines ORM models; Omolara creates Alembic migrations. Weekly Monday sync.
- **Ibrahim:** Ajibola provides auth models; Ibrahim builds RBAC enforcement.
- **Jeremiah:** Ajibola wires `EventStore`/`Simulator`; Jeremiah builds audit sink and hash chain.
- **Temi/David/Lanre:** Ajibola provides event bus + orchestrator; they plug in color teams.

---

## Exit Criteria

1. `from ciicerone.db import Base, get_session` works.
2. `Simulator.execute_simulation()` persists results and emits events.
3. `ciicerone exercise run --scenario templates/finance_bec.yaml --teams red,blue` runs end-to-end.
4. All API endpoints require auth and enforce tenant isolation.

---

## Risks

- Single point of failure for Weeks 1–14.
- Recommend pairing with Omolara on event bus and with Ibrahim on API auth.
