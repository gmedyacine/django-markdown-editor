Hi all,

I’m sharing the final outcome of the SUGAR POC: the end-to-end integration is working and validated.

**What we achieved (POC scope)**

* We validated a “personal authentication” flow using my own UID and password.
* Via **SESAME Europe**, we successfully retrieve an authentication token.
* With this token, we can call **SUGAR** directly to:

  * retrieve **document information/metadata**, and
  * download the **document file**, stored with the same filename on the Domino side.

This confirms the feasibility of a Domino ↔ SUGAR connector based on SESAME token access.

---

## Key decisions for industrialization (Architecture)

**1) Authentication strategy (to be decided)**

* **Option A — Service account (preferred for production):** stable ownership, easier lifecycle management, and clearer governance.
* **Option B — Personal accounts:** workable but creates operational dependency on individuals (rotation, departures, access scope).

We need an architecture decision on which model we adopt, and what access rights/scope are expected on the SUGAR side.

**2) Traceability & auditability (calls + document retrieval)**
Goal: enable audits on “who accessed what, when, and why”.

* Standardize structured logs for each SUGAR call (endpoint, doc_id, timestamp, status code, requester identity / account type, correlation id if available).
* Define where the **history is stored** and **how it is exploited** (retention period, searchability, export for audit requests).
* Ensure we can reconstruct the full chain for a given document: metadata request → download → storage location.

(No monitoring/runbook focus at this stage—only auditability/traceability.)

**3) Data retention & storage strategy on Domino**
We need to decide what happens to documents once retrieved into Domino:

* **Retention duration:** how long do we keep SUGAR documents in Domino datasets?
* **Lifecycle actions:** do we automatically delete after X days, archive, or encrypt?
* **Target storage (if applicable):** do we move/archive encrypted files to an object storage (e.g., COS / bucket), and keep only references/metadata in Domino?
* **Access controls:** who can read the stored files and metadata, and under which conditions? 

To avoid building a one-off implementation, the next steps should include an **abstraction layer** so the connector framework can onboard other document platforms beyond SUGAR. This will be taken into account from the start (common interfaces, pluggable backends, shared audit/retention mechanisms) to keep the solution optimized and reusable. Thibaut also suggested that we start projecting ourselves toward additional connectors, identifying potential future targets and ensuring the architecture remains flexible enough to integrate them easily.

---

## Proposed next step

I suggest a short workshop with the architects to decide:

1. **Service account vs personal accounts** for the connector
2. **Auditability approach** (logging + historical exploitation)
3. **Retention / archival / encryption strategy** for downloaded documents
4. **Abstraction approach** to support additional platforms in the same connector framework

Once these decisions are confirmed, we can consolidate the target design and the implementation plan for an industrial connector.

Thanks,
Yassine
