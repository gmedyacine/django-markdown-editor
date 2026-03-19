# [ITSVC] K3580 — Domino Log Management: LaaS (Solution A) vs Full Domino (Solution B)

**Status:** Draft  
**Author:** DataLab IT Cardif  
**Last updated:** 2026-03-19  
**Related ticket:** K3580

---

## 1. Context & Objective

All workloads deployed on the **Domino DataLab** platform (Model APIs, Jobs, Webapps) produce execution logs. These logs are critical for:

- **Operational monitoring** — detect errors, measure latency, track execution status
- **Security audit** — who accessed what, when, from which workload
- **GDPR compliance** — Model API logs may contain **sensitive medical data** (health status, age, medical records) passed as inference payloads

Two architectural solutions are evaluated in this document to address centralized log management with appropriate access control.

---

## 2. Solution A — LaaS (ELK Stack, BNP Cardif Group)

> See attached diagram: `solution-a-laas.drawio`

### 2.1 Architecture Overview

Domino workload pods (Model API, Jobs, Webapps) write logs to stdout/stderr. Kubernetes captures these logs natively. A **Filebeat DaemonSet** deployed on the cluster collects all pod logs and forwards them to the Group's **LaaS (Log as a Service)** platform, which runs an ELK stack (Elasticsearch + Logstash + Kibana).

```
Domino pod (stdout/stderr)
    └─► Kubernetes log capture
         └─► Filebeat DaemonSet (all pods, all namespaces)
              └─► [1] TCP/TLS ──► Logstash (parse + filter)
                                       └─► [2] Elasticsearch (index + store)
                                                └─► [3] Kibana (dashboard + search)
                                                         └─► [4] Users (portefeuilles LaaS)
```

### 2.2 Access Control

Access to Kibana is governed by **LaaS portefeuilles** (portfolio-based access groups managed by the Group LaaS team). In theory, Domino organisations could be mapped to LaaS portfolios to mirror the same perimeter boundaries.

### 2.3 Log Retention

**1 month** (enforced by the Group LaaS platform — not configurable by DataLab).

### 2.4 ⚠️ Red Flag — GDPR Risk

> **This is a critical architectural concern that motivated the design of Solution B.**

| Risk | Description |
|---|---|
| **Uncontrolled perimeter** | A Kibana user with a portfolio can access the logs of **all Domino Model APIs in the Group**, not just their own organisation's APIs |
| **Portfolio/Org misalignment** | LaaS portfolios are **not yet aligned** with Domino organisations — no automatic boundary enforcement |
| **Sensitive data exposure** | Model API logs contain **sensitive medical data**: health status, age, medical records, policy numbers passed as inference payloads |
| **No DataLab control** | Access control is managed by the Group LaaS team, not by DataLab IT Cardif |

---

## 3. Solution B — Full Domino Log Management

> See attached diagram: `solution-b-domino.drawio`

### 3.1 Architecture Overview

A **full-Domino** solution that leverages the Domino Platform REST API to collect, store, and expose logs — entirely within the Domino perimeter and access control model.

```
Sources:
  ├─ Domino Model API pods  ──────────────────────────────────────┐
  ├─ Domino Job pods  ────────────────────────────────────────────┤
  └─ Domino App pods  ────────────────────────────────────────────┤
                                                                   ▼
                               Domino Platform REST API
                               (internal to cluster)
                                       │
                                       ▼ [1] poll (API Key auth)
                    ┌──────────────────────────────────────────┐
                    │  Log Collector Job (Domino Job — scheduled) │
                    │  - calls Domino log APIs                   │
                    │  - filters by organisation                 │
                    │  - normalises to JSON                      │
                    │  - writes to Domino Dataset                │
                    └──────────────────────────────────────────┘
                                       │ [2] write Parquet/JSON
                                       ▼
                    ┌──────────────────────────────────────────┐
                    │  Domino Dataset: domino-logs               │
                    │  Partitioned: date / org / workload_type  │
                    │  Retention: configurable (default 30 days) │
                    └──────────────────────────────────────────┘
                                       │ [3] read (org-filtered)
                                       ▼
                    ┌──────────────────────────────────────────┐
                    │  Log Viewer Webapp (Domino App)            │
                    │  - GET /api/organizations/v1              │
                    │    → shows only user's org perimeter      │
                    │  - DataGrid · Highcharts · Filters        │
                    │  - Export CSV/JSON                        │
                    └──────────────────────────────────────────┘
                                       │
                                       ▼
                    Users (Data Scientists · Managers · Admin)
                    (access governed by Domino Org membership)
```

### 3.2 Domino APIs Used for Log Collection

The following **official Domino Platform REST API** endpoints are used by the Log Collector Job:

| API Endpoint | Log Type | Required Permission |
|---|---|---|
| `GET /api/jobs/v1/jobs/{jobId}/logs` | Job execution stdout/stderr | `ViewJobs` |
| `GET /api/modelapi/v1/{modelId}/instances/{instanceId}/logs` | Model API instance logs (request/response, latency, status) | `ModelAPIView` |
| `GET /api/audittrail/v1/...` | Platform audit events (access, permissions, dataset events) | Admin |
| `GET /api/appinstances/v1/{appId}/logs` | Domino App execution logs | `AppView` |
| `GET /api/organizations/v1` | List user's organisations (for perimeter enforcement) | None |

> **Note:** The Jobs logs and some Model API log endpoints are currently marked **beta** in the Domino API reference. Validate against your deployed Domino version before implementation.

### 3.3 Access Control — Organisation-based Perimeter (in webapp code)

The Log Viewer Webapp enforces access boundaries directly in its source code:

```python
# On user login to the webapp:
user_orgs = domino_api.get("/api/organizations/v1")  # orgs of connected user
logs = dataset.read(filter={"org": user_orgs})         # filter dataset to user's orgs only
```

- A **Data Scientist** in Org `Risk-Models` only sees logs from `Risk-Models` projects
- A **DataLab Admin** can see all organisations
- The perimeter is enforced in code — **no dependency on external portfolio management**

### 3.4 Log Storage — Domino Dataset

| Property | Value |
|---|---|
| Format | Parquet / JSON (configurable) |
| Partitioning | `date` / `org` / `workload_type` |
| Retention | Configurable (default: 30 days rolling — not capped at 1 month) |
| Access | Domino Dataset permissions (per project / organisation) |
| Location | Domino File Store (internal to platform) |

### 3.5 Log Viewer Webapp — UI Components

| Component | Purpose |
|---|---|
| DataGrid / Ag-Grid | Paginated log table with column filters, sort, search |
| Highcharts / Chart.js | Volume charts, latency trends, error rate over time |
| Filters | Organisation, workload type, date range, status |
| Export | CSV / JSON download |
| Alerts (optional) | Error threshold alerts via Domino Job notification |

---

## 4. Comparative Analysis: Solution A vs Solution B

| Criterion | Solution A — LaaS (ELK) | Solution B — Full Domino |
|---|---|---|
| **Access control** | LaaS portfolios — managed by Group team, not yet aligned with Domino orgs | Domino Organisations — managed by DataLab Admin, enforced in webapp code |
| **Sensitive data (GDPR)** | ⚠️ HIGH RISK — medical data accessible across all Group APIs in Kibana | ✅ CONTAINED — data stays within Domino perimeter, org-filtered |
| **Perimeter control** | External dependency (Group LaaS team) | Full DataLab autonomy |
| **Log retention** | 1 month (fixed by Group LaaS) | Configurable (30 days default, extendable) |
| **Setup complexity** | Low (Filebeat DaemonSet + LaaS onboarding) | Medium (Collector Job + Dataset + Webapp to build) |
| **Maintenance** | Low (managed Group service) | Medium (DataLab owns the stack) |
| **Infrastructure cost** | Included in Group LaaS | Domino compute (Collector Job + App) |
| **Visualisation** | Kibana (feature-rich, ready to use) | Custom Webapp (Highcharts / DataGrid — to build) |
| **Auditability of access** | Kibana audit (Group-level) | Domino Audit Trail (DataLab-level) |
| **Dependency** | Group LaaS availability | Domino platform availability |
| **Recommended for Cardif** | ❌ Not recommended (GDPR risk unresolved) | ✅ Recommended |

---

## 5. Recommendation

> **Solution B is recommended for DataLab Cardif.**

The primary driver is **GDPR compliance**: Model API logs contain sensitive medical data. Solution A's current portfolio/org misalignment creates an unacceptable risk of cross-team data exposure in Kibana.

Solution B eliminates this risk by keeping all log data within the Domino perimeter and enforcing org-based access control in the webapp source code — giving DataLab full autonomy over who sees what.

**Proposed implementation phases:**

| Phase | Deliverable | Priority |
|---|---|---|
| 1 | Log Collector Job (Domino Job — polls APIs, writes Dataset) | 🔴 High |
| 2 | Domino Dataset schema + partitioning strategy | 🔴 High |
| 3 | Log Viewer Webapp v1 (DataGrid + org filter) | 🟡 Medium |
| 4 | Highcharts dashboards (volume, latency, errors) | 🟡 Medium |
| 5 | Alerting on error thresholds | 🟢 Low |

---

## 6. Open Points

| # | Topic | Owner | Status |
|---|---|---|---|
| OP-1 | Validate beta status of Jobs/ModelAPI log endpoints on DataLab Domino version | DataLab DevOps | 🔴 Pending |
| OP-2 | Define Collector Job schedule frequency (5 min? real-time streaming?) | DataLab | 🔴 Pending |
| OP-3 | Choose webapp frontend stack (Python Dash/Streamlit vs React) | DataLab | 🔴 Pending |
| OP-4 | Define Dataset partitioning and retention policy with Security team | DataLab + Security | 🔴 Pending |
| OP-5 | Formally document GDPR risk of Solution A for management decision | DataLab + DPO | 🔴 Pending |
| OP-6 | Assess whether Solution A can coexist (operational logs non-sensitive) | DataLab | 🟡 Optional |

---

## 7. References

- Draw.io diagrams: `solution-a-laas.drawio`, `solution-b-domino.drawio` (attached)
- Domino Jobs API: https://docs.dominodatalab.com/en/latest/api_guide/8c929e/domino-platform-api-reference/
- Domino Audit Trail API: https://docs.dominodatalab.com/en/latest/admin_guide/a157c4/using-the-audit-trail-api/
- Domino Endpoint Logs: https://docs.dominodatalab.com/en/latest/user_guide/d788b5/model-api-health-and-logs/
- Domino Monitor Application Logs: https://docs.dominodatalab.com/en/latest/admin_guide/a9e507/monitor-application-execution-logs/
- Related Confluence pages: `[Datalab] 00 - Global Product Architecture`, `K3580 - PostGree hvault Audit and db connector`
