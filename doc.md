
### Current State: CARDX Model API Logging Architecture

**Context:** This comment documents the current mechanism used to route logs from CARDX Model APIs into the `CARDX_LOGS` dataset. By design within Domino Data Lab, published Model APIs do not have direct write access to mounted datasets.

To bypass this restriction, the Data Science team (specifically Wajih) has implemented an asynchronous logging workaround using Redis and Celery.

**How the Current Implementation Works:**

* **1. Log Generation (Model API as Producer):** Instead of writing to a local dataset directory, the Model API is configured to use Celery to push log objects (inputs, predictions, metadata) directly to an external **Redis** instance, which acts as an intermediary message broker.
* **2. Data Extraction via Domino Jobs (Consumer):** Because standard Domino Jobs *do* have write permissions to Datasets, the Data Science team runs separate, dedicated Domino Jobs to extract the data from Redis.
* **3. Worker Orchestration (`supervisord`):** Within these extraction jobs, a `supervisord` configuration is used to manage multiple **Celery workers**. Based on the `supervisord.conf` file, these workers are configured to listen to specific Redis queues corresponding to different projects and environments (e.g., `fr_dc_kyi_dev_logs`, `co_claims_prod_logs`).
* **4. Dataset Persistence:** A Python script (`supervisord_collect.py`) is executed to start the supervisor daemon. The Celery workers consume the pending log objects from the Redis queues, write them directly into the mounted **CARDX_LOGS dataset**, and then the supervisor is stopped once the execution time or queue is exhausted.

**Summary:** The current pipeline relies on the Model API acting as an asynchronous publisher to Redis, while entirely separate batch jobs (managed by the DS team) act as consumers to physically write the logs into the Domino dataset.

