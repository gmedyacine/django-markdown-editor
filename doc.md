# [ITSVC] K3580 — PostgreSQL : Vault Audit & DB Connector

**Status:** Draft  
**Author:** DataLab IT Cardif  
**Last updated:** 2026-03-18  
**Related ticket:** K3580

---

## 1. Context & Objective

DataLab workloads running inside the **Domino Data Lab** platform (Kubernetes cluster) need to retrieve secrets (credentials, API keys, config) from the **BNP Cardif Group HashiCorp Vault** instance.

Every secret access must be **auditable**: who accessed what, from which workload, at what time, and with what outcome.

This page describes the architecture of:

- PKI-based mutual authentication between Domino workloads and HashiCorp Vault
- Secret retrieval via the `hvaultconnector` Python library
- Audit trace storage in a dedicated PostgreSQL database
- Access control on PostgreSQL (writer role / reader role)
- Consumption of audit data by an audit webapp and managers

---

## 2. Components Overview

| Component | Role | Location |
|---|---|---|
| **HashiCorp Vault** | Secret store, PKI CA, policy enforcement | External — BNP Cardif Group (HTTPS only) |
| **hvaultconnector** | Python lib — PKI auth + secret fetch + audit write | Inside each Domino pod (K8s cluster) |
| **Domino Job** | Python compute workload | K8s pod — ns `domino-platform` |
| **Domino Model API** | Python FastAPI inference workload | K8s pod — ns `domino-platform` |
| **PostgreSQL** | Audit log storage (`audit_logs` table) | K8s or VM — DataLab platform |
| **Audit Webapp** | Read-only audit log viewer | To be built — DataLab team |
| **Managers / Auditors** | Human consumers of audit data | Via audit webapp only |

---

## 3. Architecture

### 3.1 Diagram

> See attached Draw.io file: `domino-hvault-audit-v2-fixed.drawio`

**Zones:**

```
┌──────────────────────────────────────────────────────────────────────┐
│  HashiCorp Vault — BNP Cardif Group (external, HTTPS only)           │
│  ┌─────────────┐ ┌──────────────┐ ┌────────────┐ ┌──────────────┐  │
│  │  Auth PKI   │ │  PKI CA Eng. │ │ KV Secrets │ │  Policy ACL  │  │
│  └─────────────┘ └──────────────┘ └────────────┘ └──────────────┘  │
│  Token: TTL-short · revocable · bound to policy                      │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│  K8s Cluster — DataLab Cardif (ns: domino-platform)                  │
│  ┌─────────────────────────┐   ┌──────────────────────────────────┐ │
│  │ pod: domino-job         │   │ pod: domino-model-api            │ │
│  │  ┌─────────────────┐   │   │  ┌────────────────────────────┐  │ │
│  │  │  Domino Job     │   │   │  │  Domino Model API          │  │ │
│  │  └────────┬────────┘   │   │  └────────────┬───────────────┘  │ │
│  │  ┌────────▼────────┐   │   │  ┌────────────▼───────────────┐  │ │
│  │  │ hvaultconnector │   │   │  │  hvaultconnector           │  │ │
│  │  └────────┬────────┘   │   │  └────────────────────────────┘  │ │
│  │  ┌────────▼────────┐   │   │  ┌────────────────────────────┐  │ │
│  │  │ Client CRT+KEY  │   │   │  │  Client CRT+KEY            │  │ │
│  │  └─────────────────┘   │   │  └────────────────────────────┘  │ │
│  └─────────────────────────┘   └──────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────┐   ┌────────────────────────────────┐
│  PostgreSQL — audit_logs     │   │  Consumers                     │
│  ┌────────────────────────┐  │   │  ┌──────────────────────────┐  │
│  │  Role: audit_writer    │  │   │  │  Audit Webapp (read-only) │  │
│  │  INSERT only           │  │◄──┤  └──────────────┬───────────┘  │
│  ├────────────────────────┤  │   │  ┌──────────────▼───────────┐  │
│  │  Role: audit_reader    │  │   │  │  Managers / Auditors     │  │
│  │  SELECT only           │  │   │  └──────────────────────────┘  │
│  └────────────────────────┘  │   └────────────────────────────────┘
└──────────────────────────────┘
```

---

### 3.2 Numbered Flows

| # | Flow | Protocol | Color in diagram |
|---|---|---|---|
| **[0]** | PKI CA Engine generates the client certificate (one-time setup) | Internal Vault | Dashed green |
| **[1]** | `hvaultconnector` loads the CRT and sends `POST /v1/auth/pki/login` to Vault | HTTPS | Dark green |
| **[2]** | Vault verifies CRT against CA + policy → returns a short-TTL token | HTTPS response | Purple |
| **[3]** | Token is used to `GET /v1/secret/data/<path>` — retrieves app secrets **and** PG writer credentials | HTTPS | Blue |
| **[4]** | `hvaultconnector` opens a PG connection (using credentials from [3]) and writes `INSERT INTO audit_logs` | TCP 5432 | Orange |
| **[5]** | Audit webapp connects to PG with reader credentials (from Vault KV) and runs `SELECT` queries | TCP 5432 | Green |
| **[6]** | Vault native Audit Device forwards Vault-side logs to PG (separate pipeline — Fluentd / Vector / microservice) | TBD | Dashed red |

---

## 4. PKI Authentication Detail

Since Vault is a **Group-level instance** (external to the K8s cluster, HTTPS access only), the authentication method is **PKI certificate-based**.

### Flow detail inside `hvaultconnector`

```
1. Load client certificate (CRT) and private key (KEY) from the pod filesystem
2. POST /v1/auth/pki/login
   Body: { "name": "<role>", "certificate": "<PEM>" }
3. Vault validates:
   a. CRT is signed by the registered PKI CA
   b. CRT common name / SAN matches the Vault PKI role
   c. CRT is not expired or revoked
4. Vault returns a Vault Token:
   - Short TTL (e.g. 15–60 min)
   - Bound to the policy associated with the PKI role
   - Revocable
5. hvaultconnector uses the token for all subsequent KV reads
6. Token is NOT stored — re-issued on each workload execution
```

### Certificate lifecycle

| Step | Owner | Tooling |
|---|---|---|
| CA setup | Vault Group team | Vault PKI Engine |
| Client CRT generation | DataLab CI/CD (GitLab) | `vault write pki/issue/<role>` |
| CRT injection into pod | Kubernetes Secret + pod mount | GitLab CI / Helm |
| CRT renewal | Before expiry | GitLab pipeline |

---

## 5. PostgreSQL Access Control

### 5.1 Why not Vault Database Engine?

The team has **read-only access** to the Group Vault instance — it is not possible to configure a Database Engine (dynamic credentials). Therefore, static credentials are stored in **Vault KV v2**.

### 5.2 KV Secret Paths

| KV Path | Content | Used by |
|---|---|---|
| `secret/datalab/audit-pg/writer` | `username` / `password` for role `audit_writer` | `hvaultconnector` |
| `secret/datalab/audit-pg/reader` | `username` / `password` for role `audit_reader` | Audit webapp |

### 5.3 PostgreSQL Roles

```sql
-- Writer: INSERT only (used by hvaultconnector)
CREATE ROLE audit_writer LOGIN PASSWORD '...';
GRANT INSERT ON audit_logs TO audit_writer;

-- Reader: SELECT only (used by audit webapp)
CREATE ROLE audit_reader LOGIN PASSWORD '...';
GRANT SELECT ON audit_logs TO audit_reader;
```

### 5.4 Vault Policies

```hcl
# Policy: datalab-audit-writer
path "secret/data/datalab/audit-pg/writer" {
  capabilities = ["read"]
}

# Policy: datalab-audit-reader
path "secret/data/datalab/audit-pg/reader" {
  capabilities = ["read"]
}
```

Each PKI role in Vault is bound to its corresponding policy. A workload that authenticates as `domino-job` can only read the writer credentials — it cannot access the reader path.

### 5.5 Network Policy (K8s)

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-postgres-from-workloads
  namespace: domino-platform
spec:
  podSelector:
    matchLabels:
      app: postgresql-audit
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: domino-workload
      ports:
        - protocol: TCP
          port: 5432
```

> **Rule:** Only pods with label `app=domino-workload` can reach PostgreSQL on port 5432. Managers and external consumers access data exclusively through the audit webapp.

---

## 6. PostgreSQL Schema

```sql
CREATE TABLE audit_logs (
    id          UUID         DEFAULT gen_random_uuid() PRIMARY KEY,
    ts          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    namespace   TEXT,                        -- e.g. domino-platform
    workload    TEXT,                        -- job | model-api
    pod_name    TEXT,
    vault_path  TEXT,                        -- /v1/secret/data/...
    action      TEXT,                        -- read | login
    status      TEXT,                        -- success | error
    duration_ms INTEGER,
    error_msg   TEXT                         -- nullable
);

-- Recommended index for webapp queries
CREATE INDEX idx_audit_logs_ts ON audit_logs (ts DESC);
CREATE INDEX idx_audit_logs_workload ON audit_logs (workload, ts DESC);
```

---

## 7. `hvaultconnector` Library

The library is a **stdlib-only Python package** (no third-party dependencies) imported directly into Domino workloads.

### Responsibilities

1. Load client CRT + KEY from pod filesystem
2. Authenticate against Vault PKI Auth Method → obtain short-TTL token
3. Retrieve secrets from Vault KV v2 using the token
4. Retrieve PostgreSQL writer credentials from Vault KV
5. Write audit trace to PostgreSQL (`INSERT INTO audit_logs`)
6. Exit with code `2` on non-blocking warnings (GitLab CI integration)

### Module structure

| Module | Responsibility |
|---|---|
| `library_rules.py` | Library-to-hardware tier mapping rules |
| `import_scanner.py` | AST-based Python import detection |
| `pattern_analyzer.py` | Code pattern analysis |
| `hw_recommender.py` | Hardware tier recommendation (7 tiers: Small → GPU X-Large) |
| `config_generator.py` | `.domino/config.yaml` + JSON report output |
| `cli.py` | Command-line entry point |

---

## 8. Credential Rotation Procedure

Since credentials are static (Vault KV, no dynamic engine):

1. Generate new password for the target PG role
2. Update the Vault KV secret at the corresponding path
3. Rolling restart of affected pods (hvaultconnector re-fetches creds at startup)
4. Verify connectivity with new credentials
5. Revoke old password from PostgreSQL

> **Recommended rotation frequency:** every 90 days, or immediately upon suspected compromise.

---

## 9. Open Points

| # | Topic | Owner | Status |
|---|---|---|---|
| OP-1 | Confirm available KV paths with Vault Group team | DataLab + Vault Group | 🔴 Pending |
| OP-2 | Define pipeline for flow [6]: Vault Audit Device → PG (Fluentd / Vector / microservice) | DataLab | 🔴 Pending |
| OP-3 | Define audit webapp stack (framework, hosting — in-cluster or external) | DataLab | 🔴 Pending |
| OP-4 | Define CRT injection mechanism into pods (K8s Secret + Helm / GitLab CI) | DataLab DevOps | 🔴 Pending |
| OP-5 | Validate credential rotation frequency and process with Security team | DataLab + Security | 🔴 Pending |

---

## 10. References

- Draw.io diagram: `domino-hvault-audit-v2-fixed.drawio` (attached)
- Vault PKI Auth documentation: https://developer.hashicorp.com/vault/docs/auth/cert
- Vault KV v2 documentation: https://developer.hashicorp.com/vault/docs/secrets/kv/kv-v2
- Domino Data Lab documentation: https://docs.dominodatalab.com
- Related Confluence pages: `[Datalab] 00 - Global Product Architecture`
