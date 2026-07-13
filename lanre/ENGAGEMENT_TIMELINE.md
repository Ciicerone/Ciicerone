# Ciicerone Engagement Timeline

> **Generated:** 2026-07-13  
> **Repo:** Ciicerone/Ciicerone  
> **Branch:** master (local) → master/main (upstream)  
> **30 open PRs** · **40+ open issues** · **9 maintainers**

---

## Phase 0: Current State (Already Merged)

### 2025 Q4 — Foundation
| Date | Feature | Owner |
|------|---------|-------|
| Sep | Initial commit — template system, CLI, multi-LLM | Foundation |
| Oct | Documentation fixes, community support | @2abet |
| Nov | Ollama local LLM, simulator enhancements | Foundation |
| Dec | Testing infrastructure | @mykael02 |
| Dec 30 | **v0.1.0 Release** — core platform shipped | Team |

### 2026 Q1 — Feature Expansion
| Date | Feature | Owner |
|------|---------|-------|
| Jan 3 | SIEM Detection Rule Generator | @ocheme1107 (David) |
| Jan 4 | SPL Injection Prevention | @ocheme1107 (David) |
| Jan 13 | ContentFilter + Kill Switch | @TemiAdebola (Temi) |
| Jan 13 | Event Sourcing Phase 1 | @TemiAdebola (Temi) |
| Jan 14 | Safety Guardrails Engine | @Shizoqua (Lanre), @bayulus (Olabisi) |
| Jan 15 | P0 Security Fixes | @bayulus (Olabisi) |
| Jan 16 | Template Security Validator (74 tests) | @bayulus (Olabisi) |
| Jan 17 | Feedback REST API, CI pipeline fixes | @jiboo2022 (Jibo) |
| Jan 17 | Docker containerization | @laradipupo (Lara) |
| Feb | MITRE ATT&CK Full Coverage Engine | @ocheme1107 (David) |
| Feb | Model Fallback Chain (LLM HA) | @Shizoqua (Lanre) |
| Feb | Batch Processing for Simulations | @jiboo2022 (Jibo) |
| Feb | Event Sourcing Phase 2 (PostgreSQL) | @jiboo2022 (Jibo) |
| Mar | Compliance Audit Framework + GDPR docs | @okino007 (Jerry) |
| Mar | RBAC Core System (merged then reverted) | Team |
| Mar | Rebrand: ThreatSimGPT → Ciicerone | Team |

---

## Phase 1: Merge Open PRs (30 PRs)

### Sprint 1.1 — CI/Infrastructure (Weeks 1-2)
| PR | Feature | Owner | Target |
|----|---------|-------|--------|
| #168 | Consolidate CLI command registration | @laradipupo | main |

### Sprint 1.2 — Database ORM + Event Sourcing (Weeks 2-4)
| PR | Feature | Owner | Target |
|----|---------|-------|--------|
| #170 | SQLAlchemy declarative base + async engine | @jiboo2022 | main |
| #178 | Alembic ORM metadata wiring | @laradipupo | main |
| #174 | DB connection pool config | @laradipupo | main |
| #172 | Wire event sourcing into simulator | @jiboo2022 | main |
| #180 | Consolidate event sourcing into Simulator | @jiboo2022 | main |
| #181 | Wire EventStore into Simulator | @jiboo2022 | main |
| #184 | Typed event definitions | @laradipupo | main |
| #185 | Event bus public API exports | @jiboo2022 | main |
| #183 | Shared async event bus (color-team comms) | @jiboo2022 | main |

### Sprint 1.3 — Audit + Compliance (Weeks 3-5)
| PR | Feature | Owner | Target |
|----|---------|-------|--------|
| #204 | Audit event ORM model | @okino007 | main |
| #205 | Audit events migration | @okino007 | main |
| #150 | GDPR breach notification templates | @okino007 | master |
| #151 | Audit framework overview + logging policy PDFs | @okino007 | master |

### Sprint 1.4 — Blue/Red Team Features (Weeks 4-6)
| PR | Feature | Owner | Target |
|----|---------|-------|--------|
| #149 | Intelligence-driven hypothesis generator | @ocheme1107 | master |
| #157 | Approval workflows + audit logging | @AdebolaH | master |
| #154 | Core API Gateway | @laradipupo | master |
| #152 | Enhanced RAG retriever error handling | @laradipupo | master |
| #176 | Azure OpenAI embedding + Neo4j fix | @laradipupo | main |
| #140 | AttackAgent single command state tracking | @AdebolaH | master |

### Sprint 1.5 — Scenario/Difficulty + Security (Weeks 5-7)
| PR | Feature | Owner | Target |
|----|---------|-------|--------|
| #144 | Enhanced Scenario Engine | @TemiAdebola | master |
| #146 | Adaptive Difficulty Engine | @TemiAdebola | master |
| #142 | MITRE ATT&CK Full Coverage (production-ready) | @ocheme1107 | master |
| #139 | Refactor Template Security Validator | @TemiAdebola | master |
| #212 | Eliminate N+1 query in graph enrichment | @TemiAdebola | master |
| #211 | Unit tests for air-gap model download | @Shizoqua | main |
| #209 | Llama.cpp local-only verification | @Shizoqua | main |
| #208 | Gate external model downloads (air-gap) | @Shizoqua | main |

---

## Phase 2: Commit Local Changes (Unstaged Work)

### Sprint 2.1 — Infrastructure-as-Code (Weeks 6-8)
| Area | Items |
|------|-------|
| **Helm** | ciicerone/ — Kubernetes Helm charts |
| **K8s** | ConfigMap, Deployment, Ingress, Namespace, Secret, Service |
| **Terraform** | Multi-environment IaC (main.tf, modules, envs) |
| **Docker** | Grafana, Nexus, Postgres, Prometheus, SonarQube |
| **docker-compose.yml** | Full local stack (159 lines) |
| **Makefile** | Build automation (176 lines) |

### Sprint 2.2 — Platform Expansion (Weeks 7-9)
| Area | Items |
|------|-------|
| **Frontend** | HTML/CSS/JS web UI (Lara) |
| **Collaboration** | Kafka pub/sub, WebSocket handler, room manager (Jibo) |
| **Review C1** | **Jibo + Lara sync on collaboration API contract** before frontend build |
| **Flink Streaming** | Apache Flink CEP job on event stream for threat pattern detection (Jibo) |
| **API Expansion** | New routers (collaboration), expanded main.py (Lara) |
| **E2E Tests** | 10 test files: API/CLI/config/DB/collab WS/Kafka/security/simulation/LLM/analytics |

### Sprint 2.3 — CI/Infra + Maintainer Tooling (Week 8-9)
| Area | Items |
|------|-------|
| **CI Workflow** | 520-line expansion, deploy.yml, dependabot.yml (Jibo) |
| **Pipeline hardening** | Test automation, code coverage gates |
| Maintainer SSH scripts | maintainer-git.sh, setup-maintainers.sh, agent-git.sh, agent-setup.sh |
| Docs | SSH maintainer guides (2 files) |
| CODEOWNERS | 9 maintainers assigned |
| .opencode/ | OpenCode configuration |

---

## Phase 3: Planned Features (Open Issues)

### Sprint 3.1 — Audit & Compliance System (Weeks 8-10)
| Issue | Feature | Priority |
|-------|---------|----------|
| #186 | Audit event ORM model | high |
| #187 | Audit events DB migration | high |
| #188 | Database audit sink with hash-chain | high |
| #189 | Async logging for AuditLogger | high |
| #190 | Audit event verification | medium |
| #191 | Audit event router | medium |
| #192 | Export audit router | medium |
| #193 | Register audit router in FastAPI | medium |
| #194 | MITRE + compliance fields to ThreatScenario | high |
| #195 | Rules of Engagement engine | high |
| #196 | Wire audit + RoE into Simulator | high |
| #197 | MITRE-to-framework compliance mapper | high |
| #198 | Compliance report generator | high |
| #199 | Compliance ORM models | high |
| #200 | Compliance tables migration | high |
| #201–203 | Unit tests (ComplianceMapper, DatabaseAuditSink, RoE) | medium |
| #207, #210 | Air-gap model unit tests | medium |

### Sprint 3.2 — Core Refinements (Weeks 10-12)
| Issue | Feature | Priority |
|-------|---------|----------|
| #131 | VMOperator Screenshot refactor | high |
| #132 | AttackAgent Single Command redesign | high |
| #158 | Local model support (Ollama) | medium |
| #164 | Azure OpenAI provider | medium |
| #167 | CLI command registration consolidation | low |

### Sprint 3.3 — Advanced Capabilities (Weeks 12-16)
| Issue | Feature | Priority |
|-------|---------|----------|
| #141 | MITRE ATT&CK Full Coverage (production-ready) | high |
| #143 | Enhanced Scenario Engine | high |
| #145 | Adaptive Difficulty Engine | high |
| #147 | Attack Scenario Generator (hierarchical config) | high |
| #148 | Automated threat hunting hypothesis generation | high |
| #153 | Core API Gateway Service | high |
| #156 | Approval workflows + audit logging (blue team) | high |
| #175 | Azure OpenAI embedding + Neo4j vector store fix | medium |

---

## Maintainer Role Map

| Handle | Name | Role | Sprint Focus |
|--------|------|------|-------------|
| @jiboo2022 | Jibo | Co-Core Dev (Backend) | 1.2 (Event Bus/Sourcing), 2.2 |
| @laradipupo | Lara | Co-Core Dev | 1.2 (Events), 1.4 (API Gateway), 2.2 |
| @Shizoqua | Lanre | AI/ML Lead | 1.5 (Air-gap), 3.2 (Local models) |
| @TemiAdebola | Temi | Red Team Lead | 1.5 (Scenario/Difficulty Engines) |
| @bayulus | Olabisi | Red Team | 1.5 (Security validation) |
| @ocheme1107 | David | Blue Team | 1.4 (Hypothesis generator) |
| @AdebolaH | Ibrahim | Threat Hunting/TM | 1.4 (Approval workflows) |
| @BlessingOUdoh-ui | Blessing | SOC Lead | 3.1 (Audit, RoE, Compliance) |
| @okino007 | Jerry | Compliance | 1.3 (Audit/Compliance), 3.1 |

---

## Key Milestones

| Milestone | Target | Deliverable |
|-----------|--------|-------------|
| M1 | Week 2 | All CI/infra PRs merged |
| M2 | Week 4 | Event sourcing + DB ORM fully wired |
| M3 | Week 5 | Audit/Compliance foundation in place |
| M4 | Week 6 | All open PRs merged |
| M5 | Week 8 | Local IaC committed (Helm, K8s, Terraform, Docker) |
| C1 | Week 7–8 | Review checkpoint: Jibo + Lara sync collaboration API contract |
| M6 | Week 9 | Frontend + Collaboration + Flink streaming + E2E tests committed |
| M7 | Week 10 | Maintainer tooling finalized |
| M8 | Week 12 | Audit/RoC/Compliance feature set complete |
| M9 | Week 14 | Core refactors complete |
| M10 | Week 16 | Advanced capabilities shipped |

---

## Quick Start Commands

```bash
# Sync upstream
git fetch origin
git merge origin/master --ff-only

# Review an open PR locally
gh pr checkout <number>

# Commit as a specific maintainer
./maintainer-git.sh <handle> commit -m "feat: ..."

# Test SSH auth for a maintainer
ssh -T git@github-<handle>
```
