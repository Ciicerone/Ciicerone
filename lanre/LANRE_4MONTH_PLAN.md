# Lanre — 4-Month High-Impact Plan

**@hrlanreshittu · AI/ML Lead**  
**Goal:** ~5 meaningful commits/month · 20 total · sequenced for maximum velocity

---

## Month 1 — Air-Gap Security

*Blocks data exfiltration vectors before any model work begins — security-first.*

| # | Commit | PR/Issue | Impact |
|---|--------|----------|--------|
| 1 | Unit tests for air-gap model download blocking | [#211](https://github.com/Ciicerone/Ciicerone/pull/211) | Regression-proof — air-gap stays effective across refactors |
| 2 | Llama.cpp local-only model verification | [#209](https://github.com/Ciicerone/Ciicerone/pull/209) | Offline guarantee — llama.cpp never reaches external endpoints |
| 3 | Gate external model downloads in air-gap mode | [#208](https://github.com/Ciicerone/Ciicerone/pull/208) | Enforcement — single switch kills all outbound model fetches |
| 4 | Air-gap mode configuration schema | Enhancement | Declarative policy — YAML-defined air-gap rules per deployment |
| 5 | Air-gap integration test suite | Enhancement | Confidence — automated tests for every air-gap enforcement point |

---

## Month 2 — Local Model Infrastructure

*Enables fully offline operation with Ollama and a unified model abstraction.*

| # | Commit | PR/Issue | Impact |
|---|--------|----------|--------|
| 6 | Ollama integration for local model support | [#158](https://github.com/Ciicerone/Ciicerone/issues/158) | Zero-cost inference — no API keys needed for basic scenarios |
| 7 | Azure OpenAI provider support | [#164](https://github.com/Ciicerone/Ciicerone/issues/164) | Enterprise cloud — unlocks Azure customers with existing contracts |
| 8 | Model registry abstraction layer | Enhancement | Provider-agnostic — swap OpenAI ↔ Azure ↔ Ollama without code changes |
| 9 | Model download manager with air-gap awareness | Enhancement | Smart caching — downloads once, respects air-gap policy, verifies checksums |
| 10 | Local model benchmark suite | Enhancement | Performance baseline — latency, throughput, memory usage per model |

---

## Month 3 — Embedding Pipeline & RAG

*Optimizes the retrieval pipeline for accuracy and speed.*

| # | Commit | PR/Issue | Impact |
|---|--------|----------|--------|
| 11 | Azure OpenAI embedding support + Neo4j fix | [#175](https://github.com/Ciicerone/Ciicerone/issues/175) | Production RAG — Azure embeddings + reliable graph vector store |
| 12 | Embedding pipeline batch processing | Enhancement | Throughput — process 1000s of documents without OOM |
| 13 | Model fallback chain improvements | Enhancement | HA — automatic failover across provider tiers (Ollama → Azure → OpenAI) |
| 14 | ML model caching layer | Enhancement | Latency — hot cache for frequently used models, LRU eviction |
| 15 | Model health monitoring + alerting | Enhancement | Reliability — detect model degradation, auto-restart, alert on failures |

---

## Month 4 — MLOps & Knowledge Transfer

*Operationalizes the ML stack and enables other maintainers.*

| # | Commit | PR/Issue | Impact |
|---|--------|----------|--------|
| 16 | Model deployment automation (CI/CD for models) | Enhancement | Velocity — push model config changes through the same pipeline as code |
| 17 | ML pipeline monitoring dashboards (Grafana) | Enhancement | Visibility — model latency, error rates, cache hit ratios at a glance |
| 18 | RAG performance tuning + chunking strategy | Enhancement | Accuracy — optimal chunk size, overlap, embedding dimension tuning |
| 19 | Model versioning + rollback strategy | Enhancement | Safety — pin model versions, A/B test, rollback on regression |
| 20 | ML system architecture documentation | Knowledge transfer | Autonomy — any maintainer can add a new model provider |

---

## Month-by-Month Summary

```
Month 1         Month 2         Month 3         Month 4
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ Air-gap      │ │ Ollama      │ │ Azure Embed │ │ MLOps       │
│ tests        │ │ Azure Prov  │ │ Batch Embed │ │ Dashboards  │
│ Llama.cpp    │ │ Model Reg   │ │ Fallback    │ │ RAG tuning  │
│ Gate control │ │ Downloader  │ │ Caching     │ │ Versioning  │
│ Config       │ │ Benchmarks  │ │ Monitoring  │ │ Docs        │
│ 5 commits    │ │ 5 commits   │ │ 5 commits   │ │ 5 commits   │
└─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
```

**High-impact sequencing:**
- Month 1 locks down security — air-gap is a hard requirement for air-gapped deployments
- Month 2 delivers local + cloud model options — unblocks all scenario generation
- Month 3 optimizes the embedding pipeline — directly impacts RAG quality
- Month 4 operationalizes — monitoring, versioning, and docs for team autonomy
