# Internal Brief — Omolara Oladipupo

**Role:** Infrastructure Lead  
**GitHub:** @laradipupo  
**Color Team:** Yellow / Green  
**Active Window:** Weeks 1–20

---

## Mission

Own the deployment-layer infrastructure: database hardening, migrations, air-gap egress controls, and the Yellow/Green teams.

---

## Atomic Tasks

### Phase 0 — Foundation (Weeks 1–4)

| Task | Weeks | Deliverable | Unblocks |
|------|-------|-------------|----------|
| OMOLARA-001 | 1–2 | Harden PostgreSQL Docker Compose; backup/restore scripts | Persistence infrastructure |
| OMOLARA-002 | 3–4 | Alembic migration for core persistence tables | Domain model deployment |

### Phase 1 — Security & Air-Gap (Weeks 5–8)

| Task | Weeks | Deliverable | Unblocks |
|------|-------|-------------|----------|
| OMOLARA-003 | 5–8 | Migrations for auth, tenancy, audit, all domain tables | Production deployment |
| OMOLARA-004 | 7–8 | Network-level egress controls for air-gapped mode | P0-7 "no data leaves" |

### Phase 3 — Team Completion (Weeks 15–18)

| Task | Weeks | Deliverable | Unblocks |
|------|-------|-------------|----------|
| OMOLARA-005 | 15–16 | Yellow Team: secure build validation (`core/secure_build_engine.py`) | P0-2, P2-1 |
| OMOLARA-006 | 17–18 | Green Team: remediation tracking (`core/remediation_engine.py`) | P0-2, P2-1 |

### Phase 4 — Pilot Validation (Weeks 19–20)

| Task | Weeks | Deliverable |
|------|-------|-------------|
| OMOLARA-007 | 19–20 | Air-gapped deployment, migrations, backup/restore verification |

---

## Key Collaboration Points

- **Ajibola:** Ajibola defines ORM models; Omolara creates migrations. Weekly Monday sync.
- **Lanre:** Coordinate air-gap model bundle with network egress controls.
- **Jeremiah/Ibrahim:** Provide DB migrations for audit, auth, and blue-team tables.

---

## Exit Criteria

1. PostgreSQL data persists across container restarts.
2. All new tables have Alembic migrations.
3. `AIR_GAPPED_MODE=true` blocks external egress.
4. Yellow/Green teams participate in the exercise orchestrator.

---

## Risks

- Migration coordination depends on Ajibola's model definitions.
- Air-gap network policy must be tested in a real K8s/Docker environment.
