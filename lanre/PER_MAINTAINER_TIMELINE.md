# Per-Maintainer Engagement Timeline

> **Generated:** 2026-07-13  
> **Reference:** docs/ENGAGEMENT_TIMELINE.md for full context

---

## 1. Jibo (@jiboo2022) — Co-Core Dev (Backend)

**Role:** Backend core systems — event sourcing, database ORM, event bus, collaboration infrastructure, real-time streaming.

| Week | Sprint | Tasks |
|------|--------|-------|
| 2–4 | **1.2 — DB ORM + Event Sourcing** | |
| | | PR #170 — SQLAlchemy declarative base + async engine factory |
| | | PR #172 — Wire event sourcing into simulator + fix race condition |
| | | PR #180 — Consolidate event sourcing into Simulator (supersedes #172) |
| | | PR #181 — Wire EventStore into Simulator for event emission |
| | | PR #183 — Shared async event bus for color-team communication |
| | | PR #185 — Export event bus public API |
| 6–8 | **2.1 — Infrastructure-as-Code** | |
| | | Helm charts (ciicerone/) |
| | | K8s manifests (ConfigMap, Deployment, Ingress, Namespace, Secret, Service) |
| | | Terraform multi-environment IaC (main.tf, modules, envs) |
| | | Docker Compose full local stack (159 lines) |
| | | Makefile build automation (176 lines) |
| 7–8 | **2.2a — Platform Expansion: Collaboration** | |
| | | Collaboration module — Kafka pub/sub producer/consumer |
| | | Collaboration module — WebSocket handler + room manager |
| | | Collaboration module — Data models + API integration |
| | | **Review checkpoint** — Jibo + Lara sync on collaboration API contract (routes, message schemas, WS event types) before Lara builds frontend |
| | | Collaboration module — Apache Flink streaming job: CEP for threat pattern detection on event stream |
| 8–9 | **2.2b — Platform Expansion: E2E Tests** | |
| | | E2E test file 1: API health + scenario lifecycle |
| | | E2E test file 2: CLI command registration + execution |
| | | E2E test file 3: Config loading + YAML validation |
| | | E2E test file 4: Database ORM + migration |
| | | E2E test file 5: Collaboration WebSocket connect/disconnect/message |
| | | E2E test file 6: Collaboration Kafka produce/consume |
| | | E2E test file 7: Security (template injection, air-gap, auth) |
| | | E2E test file 8: Simulation execution + event emission |
| | | E2E test file 9: LLM provider chain + fallback |
| | | E2E test file 10: Feedback loop + analytics pipeline |
| 9 | **2.3 — CI/Infra & Streaming** | |
| | | CI workflow expansion (520 lines) |
| | | deploy.yml + dependabot.yml |
| | | Pipeline hardening + test automation |
| | | Performance: event sourcing batch processing |
| | | Tech debt: typed event validation + error boundaries |
| | | Documentation: event system architecture + API reference |
| | | Maintainer SSH scripts (maintainer-git.sh, setup-maintainers.sh, agent-git.sh, agent-setup.sh) |
| | | SSH maintainer guides (2 docs) |
| | | CODEOWNERS (9 maintainers) |
| | | .opencode/ configuration |
| 8–10 | **3.1 — Audit System** | |
| | | Issue #188 — Database audit sink with hash-chain support |
| | | Issue #189 — Async logging support for AuditLogger |
| | | Issue #196 — Wire audit logging and RoE into Simulator |
| 10–12 | **3.2 — Core Refinements** | |
| | | Issue #131 — VMOperator Screenshot refactor |
| | | Issue #132 — AttackAgent Single Command redesign |

**Total: ~12 PRs merged + 5 issues closed + collaboration, Flink, E2E, CI/infra, IaC, maintainer tooling**

---

## 2. Lara (@laradipupo) — Co-Core Dev (Backend)

**Role:** Backend core — CLI, API gateway, RAG, database config, typed events, Azure integration, frontend UI.

| Week | Sprint | Tasks |
|------|--------|-------|
| 1–2 | **1.1 — CI/Infrastructure** | |
| | | PR #168 — Consolidate CLI command registration |
| 2–4 | **1.2 — DB ORM + Event Sourcing** | |
| | | PR #178 — Wire Alembic target metadata to ORM Base |
| | | PR #174 — Add database connection pool configuration to config loader |
| | | PR #184 — Add typed event definitions for shared event bus |
| 4–6 | **1.4 — Blue/Red Team Features** | |
| | | PR #154 — Core API Gateway Service |
| | | PR #152 — Enhanced RAG retriever error handling |
| | | PR #176 — Azure OpenAI embedding support + Neo4j vector store fix |
| 7–9 | **2.2 — Platform Expansion** | |
| | | API expansion — new routers (collaboration), expanded main.py |
| | | Frontend — HTML/CSS/JS web UI integration |
| | | **Review checkpoint** — Sync with Jibo on collaboration API contract before building frontend |
| 10–12 | **3.2 — Core Refinements** | |
| | | Issue #167 — CLI command registration consolidation |
| | | API Gateway: rate limiting + auth middleware |
| | | API monitoring: Prometheus metrics + health endpoints |
| | | OpenAPI spec generation + Swagger/ReDoc docs |
| | | Integration test suite for API Gateway |
| 12–16 | **3.3 — Advanced Capabilities** | |
| | | Issue #153 — Core API Gateway Service implementation |
| | | API versioning strategy (v1/v2 prefix) |
| | | API request/response contract tests |
| | | Developer onboarding guide + API reference |
| | | Performance benchmark suite for API & RAG |

**Total: ~7 PRs merged + 2 issues + platform expansion + API hardening**

---

## 3. Lanre (@Shizoqua) — AI/ML Lead

**Role:** LLM integration, air-gap security, local model support, Azure OpenAI, MLOps.

| Week | Sprint | Tasks |
|------|--------|-------|
| 5–7 | **1.5 — Scenario/Difficulty + Security** | |
| | | PR #211 — Unit tests for air-gap model download blocking |
| | | PR #209 — Enforce local-only model verification for llama.cpp |
| | | PR #208 — Gate external model downloads when air-gap mode is enabled |
| | | Air-gap mode configuration schema (YAML-defined rules) |
| | | Air-gap integration test suite |
| 8–10 | **3.1 — Air-Gap Model Hardening** | |
| | | Issue #207 — Air-gap model unit tests |
| | | Issue #210 — Air-gap model unit tests |
| 10–12 | **3.2 — Core Refinements** | |
| | | Issue #158 — Local model support with Ollama integration |
| | | Issue #164 — Azure OpenAI provider support |
| | | Model registry abstraction layer (provider-agnostic) |
| | | Model download manager with air-gap awareness |
| | | Local model benchmark suite (latency, throughput, memory) |
| | | Embedding pipeline batch processing |
| | | Model fallback chain improvements (Ollama → Azure → OpenAI) |
| | | ML model caching layer (LRU eviction) |
| | | Model health monitoring + alerting |
| 12–16 | **3.3 — Advanced Capabilities** | |
| | | Issue #175 — Azure OpenAI embedding + Neo4j vector store fix |
| | | Model deployment automation (CI/CD for models) |
| | | ML pipeline monitoring dashboards (Grafana) |
| | | RAG performance tuning + chunking strategy |
| | | Model versioning + rollback strategy |
| | | ML system architecture documentation |

**Total: 3 PRs merged + 5 issues + 14 additional deliverables**

---

## 4. Temi (@TemiAdebola) — Red Team Lead

**Role:** Offensive security — scenario engines, difficulty adaptation, template security, attack generation.

| Week | Sprint | Tasks |
|------|--------|-------|
| 5–7 | **1.5 — Scenario/Difficulty + Security** | |
| | | PR #144 — Enhanced Scenario Engine for detection-optimized threat simulation |
| | | PR #146 — Adaptive Difficulty Engine for enhanced scenario generation |
| | | PR #139 — Refactor Template Security Validator (Issue #129) |
| | | PR #212 — Eliminate N+1 query in graph enrichment |
| | | Scenario template library (20+ templates: phishing, BEC, supply chain, ransomware) |
| | | Scenario validation pipeline |
| | | Scenario unit + integration test suite |
| | | Scenario authoring guide + template reference |
| 8–10 | **3.1 — Difficulty & Template Hardening** | |
| | | Difficulty calibration data collection |
| | | User skill profiling model |
| | | Difficulty progression tiers (beginner → expert) |
| | | Adaptive scenario A/B test framework |
| | | Template injection prevention test suite (100+ test cases) |
| | | Template sandboxing (safe evaluation context) |
| | | Template version diff + audit trail |
| | | Red team operational playbooks |
| 12–16 | **3.3 — Advanced Capabilities** | |
| | | Issue #143 — Enhanced Scenario Engine |
| | | Issue #145 — Adaptive Difficulty Engine |
| | | Issue #147 — Attack Scenario Generator with hierarchical config |
| | | Scenario composition engine (mix-and-match techniques, payloads, delivery) |
| | | MITRE ATT&CK technique-to-scenario mapping |
| | | Scenario marketplace / import-export format (YAML) |
| | | Red team complete simulation cookbook |

**Total: 4 PRs merged + 3 issues + 16 additional deliverables**

---

## 5. Olabisi (@bayulus) — Red Team (Security)

**Role:** Security validation, template security, guardrails engineering, penetration testing, SAST.

| Week | Sprint | Tasks |
|------|--------|-------|
| 5–7 | **1.5 — Scenario/Difficulty + Security** | |
| | | Review PR #139 — Template Security Validator refactor |
| | | Security audit of all Phase 1 PRs (SAST + manual review) |
| | | Security test coverage expansion (boundary + fuzz) |
| | | Bandit/ruff security rules review + update |
| | | Security contribution guide + threat model |
| 8–10 | **3.1 — Compliance & Guardrails** | |
| | | Issue #203 — Unit tests for RulesOfEngagement |
| | | Guardrails engine: RateLimiter + CircuitBreaker hardening |
| | | Guardrails comprehensive test suite |
| | | Guardrails performance benchmark + optimization (<5ms latency) |
| | | Guardrails configuration schema + validation |
| | | Guardrails integration tests with Simulator |
| 10–12 | **3.2 — Security Hardening** | |
| | | API security penetration testing (auth, injection, SSRF, OWASP Top 10) |
| | | Input validation hardening pass |
| | | Secret scanning automation (truffleHog, Gitleaks) |
| | | Dependency vulnerability scanning (pip-audit, Dependabot) |
| 12–16 | **3.3 — Advanced Capabilities** | |
| | | Security validation for new scenario/difficulty engines |
| | | Penetration testing of air-gap enforcement (#208, #209) |
| | | Security regression test suite (automated in CI) |
| | | Security incident response playbook |
| | | Security best practices guide for maintainers |
| | | Final security audit report before release |

**Total: Review + 1 issue + 17 additional security deliverables**

---

## 6. David (@ocheme1107) — Blue Team

**Role:** Defensive security — detection rules, hypothesis generation, MITRE ATT&CK coverage, SIEM integration.

| Week | Sprint | Tasks |
|------|--------|-------|
| 4–6 | **1.4 — Blue/Red Team Features** | |
| | | PR #149 — Intelligence-driven hypothesis generator for automated threat hunting |
| | | Hypothesis validation pipeline (scores by likelihood, impact, detectability) |
| 5–7 | **1.5 — Scenario/Difficulty + Security** | |
| | | PR #142 — MITRE ATT&CK Full Coverage - Production Ready (#141) |
| | | Detection rule expansion (20+ new Sigma rules) |
| | | SIEM integration test suite (Splunk/Sentinel/ELK) |
| | | Detection rule CI pipeline (validate on commit) |
| | | MITRE technique-to-detection matrix (coverage per tactic) |
| | | Coverage gap analysis report (prioritized undetected techniques) |
| | | Detection rule test suite (MITRE-aligned) |
| | | MITRE navigation layer in CLI/API |
| 10–12 | **3.2 — Detection Quality** | |
| | | Detection performance benchmarking |
| | | False positive reduction pass (threshold tuning, suppression) |
| | | Alert correlation rules (groups related alerts into incidents) |
| | | Detection benchmarking dashboard (detection rate, FP rate, MTTD) |
| 12–16 | **3.3 — Advanced Capabilities** | |
| | | Issue #141 — MITRE ATT&CK Full Coverage (production-ready) |
| | | Issue #148 — Automated threat hunting hypothesis generation |
| | | Hunting playbook automation engine (parameterized playbooks) |
| | | Threat intel feed integration (PhishTank, AlienVault, MISP) |
| | | SOC dashboard: detection coverage + hunt status |
| | | Blue Team detection engineering guide |

**Total: 2 PRs merged + 2 issues + 16 additional detection/integration deliverables**

---

## 7. Ibrahim (@AdebolaH) — Threat Hunting & Threat Modelling Lead

**Role:** Threat hunting workflows, authorization systems, attack agent state management, RBAC/ABAC.

| Week | Sprint | Tasks |
|------|--------|-------|
| 4–6 | **1.4 — Blue/Red Team Features** | |
| | | PR #157 — Approval workflows + audit logging system (1,012 additions) |
| | | PR #140 — AttackAgent single command state tracking fix |
| | | Workflow configuration system (YAML-defined chains) |
| | | Approval chain data models + persistence |
| | | Authorization test suite (all approval chain permutations) |
| | | Workflow documentation + operator guide |
| 8–10 | **3.1 — State & Replay** | |
| | | AttackAgent comprehensive test coverage |
| | | Attack state machine formal model |
| | | Attack replay capability (deterministic re-run) |
| | | Attack scenario validation against state model |
| 12–16 | **3.3 — Advanced Capabilities** | |
| | | Issue #156 — Approval workflows and audit logging for blue team ops |
| | | Threat hunting workflow integration with authorization |
| | | Threat intelligence pipeline with approval gates |
| | | Hunting playbook automation with auth checks |
| | | Threat detection correlation with workflow state |
| | | Authorization policy engine (RBAC + ABAC) |
| | | Audit trail viewer (who approved what, when) |
| | | Threat hunting dashboard (active hunts, findings) |
| | | Threat model library (STRIDE, PASTA, LINDDUN) |
| | | Threat modelling + authorization architecture docs |

**Total: 2 PRs merged + 1 issue + 16 additional workflow/auth deliverables**

---

## 8. Blessing (@BlessingOUdoh-ui) — SOC Lead

**Role:** SOC operations, monitoring, audit, compliance, rules of engagement.

| Week | Sprint | Tasks |
|------|--------|-------|
| 8–10 | **3.1 — Audit & Compliance System** | |
| | | Issue #186 — Audit event ORM model |
| | | Issue #187 — Audit events DB migration |
| | | Issue #190 — Audit event verification (hash-chain integrity check) |
| | | Issue #191 — Audit event router (REST API with filtering/pagination) |
| | | Issue #192 — Export audit router from routers package |
| | | Issue #193 — Register audit router in FastAPI app |
| | | Issue #194 — Add MITRE + compliance fields to ThreatScenario |
| | | Issue #195 — Rules of Engagement engine |
| | | Issue #196 — Wire audit logging and RoE into Simulator |
| | | Issue #197 — MITRE-to-framework compliance mapper |
| | | Issue #198 — Compliance report generator |
| | | Issue #201 — Unit tests for ComplianceMapper |
| | | Issue #202 — Unit tests for DatabaseAuditSink |
| | | Issue #203 — Unit tests for RulesOfEngagement |
| | | Audit query API (filter by actor, action, date, severity) |
| 12–16 | **3.3 — SOC Dashboards** | |
| | | SOC monitoring dashboards (Grafana) — audit overview + alert timeline |
| | | Alert rule definitions for SOC operations |
| | | Real-time collaboration monitoring (active rooms, msg/min, WebSocket connections) |

**Total: ~14 issues closed + 2 additional SOC dashboards**

---

## 9. Jerry (@okino007) — Compliance Lead

**Role:** Compliance framework, GDPR, audit models, ORM migrations, regulatory mapping.

| Week | Sprint | Tasks |
|------|--------|-------|
| 3–5 | **1.3 — Audit + Compliance** | |
| | | PR #204 — Audit event ORM model (additions) |
| | | PR #205 — Audit events DB migration |
| | | PR #150 — GDPR breach notification templates PDF |
| | | PR #151 — Audit framework overview + logging policy PDFs |
| | | Breach notification workflow automation |
| | | Data Processing Agreement (DPA) templates (Art. 28) |
| | | Data Subject Rights framework (Art. 12-23: access, deletion, portability) |
| | | Privacy notice documentation for platform |
| 8–10 | **3.1 — Audit & Compliance System** | |
| | | Issue #199 — Compliance ORM models |
| | | Issue #200 — Compliance tables DB migration |
| | | Compliance monitoring dashboard (Grafana, real-time posture) |
| | | Compliance control framework documentation (GDPR, SOC 2, ISO 27001, NIST CSF) |
| | | Compliance reporting templates (GDPR, SOC 2, ISO) |
| | | Regulatory mapping matrix (control-to-regulation cross-reference) |
| | | Compliance evidence collection automation (audit logs, configs, deployments) |
| 10–12 | **3.2 — Core Refinements** | |
| | | Compliance documentation updates |
| | | Audit log review procedures + automation (scheduled reviews, anomaly detection) |
| | | Vendor risk assessment templates |
| | | Compliance training materials for maintainers |
| | | Final compliance audit readiness report |

**Total: 4 PRs merged + 2 issues + 13 additional compliance deliverables**

---

## Summary: Sprint Load by Maintainer

| Maintainer | Phase 1 (PRs) | Phase 2 (Local) | Phase 3 (Issues + Additions) | Peak Sprint |
|------------|:------------:|:--------------:|:---------------------------:|:-----------:|
| Jibo | 6 | Heavy (collab, Flink, E2E, CI, IaC, tooling) | 5 + 4 additions | 2.2 (Wk 7–9) |
| Lara | 6 | Medium | 2 + 9 additions | 3.2 (Wk 10–12) |
| Lanre | 3 | — | 5 + 14 additions | 3.2 (Wk 10–12) |
| Temi | 4 | — | 3 + 16 additions | 3.3 (Wk 12–16) |
| Olabisi | Review | — | 1 + 17 additions | 3.2 (Wk 10–12) |
| David | 2 | — | 2 + 16 additions | 3.3 (Wk 12–16) |
| Ibrahim | 2 | — | 1 + 16 additions | 3.3 (Wk 12–16) |
| Blessing | — | — | 14 + 2 additions | 3.1 (Wk 8–10) |
| Jerry | 4 | — | 2 + 13 additions | 3.1 (Wk 8–10) |

## Cross-Maintainer Review Checkpoints

| Checkpoint | Week | Participants | Purpose |
|------------|------|-------------|---------|
| C1 | 7 | Jibo + Lara | Collaboration API contract: agree on WS routes, message schemas, event types before Lara builds frontend |
| C2 | 9 | Jibo + Blessing | Audit event schema handoff: Jibo's event bus output → Blessing's audit pipeline input |
| C3 | 10 | Blessing + Jerry | Compliance ORM alignment: ensure audit fields match compliance reporting requirements |
| C4 | 12 | Temi + David | Scenario-to-detection mapping: Temi's scenario output → David's detection rule input |
| C5 | 14 | All | Integration test review: validate end-to-end flows across all tracks |

## Parallel Tracks

```
Week:  1  2  3  4  5  6  7  8  9  10 11 12 13 14 15 16
      ┌──────────────────────────────────────────────────────────┐
Jibo  │████ 1.2 ████│████ 2.2a ███│█ 2.2b █│█ 2.3 █│████│██ 3.2│
      ├──────────────────────────────────────────────────────────┤
Lara  │█│███ 1.2 ███│████ 1.4 ████│█████ 2.2 █████│████ 3.2 ████│
      ├──────────────────────────────────────────────────────────┤
Lanre │                     │█████ 1.5 █████│██ 2.2 ██│██ 3.1 ██│██████│
      ├──────────────────────────────────────────────────────────┤
Temi  │                     │█████ 1.5 █████││████████ 3.3 ████████│
      ├──────────────────────────────────────────────────────────┤
David │                     │██ 1.4 ██│████ 1.5 ████││████ 3.3 ███│
      ├──────────────────────────────────────────────────────────┤
Ibrahim│                    │██████ 1.4 ██████││████████ 3.3 ████████│
      ├──────────────────────────────────────────────────────────┤
Bless.│                                  │████████████ 3.1 ████████████│
      ├──────────────────────────────────────────────────────────┤
Jerry │         │█████ 1.3 █████││████████ 3.1 ████████││││││││││││
      ├──────────────────────────────────────────────────────────┤
Olabisi│                    │████ 1.5 ████││████ 3.1 ████│████││││││
      └──────────────────────────────────────────────────────────┘
      │ C1        │C2 │C3        │C4       │C5
Legend: █ active sprint  │ sprint boundary  C# = review checkpoint
```
