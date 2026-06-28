# Project Glossary & End-User Guide

This document defines the core terminology used in the **Distributed ThreadMail System** (`shikibo`) and provides step-by-step instructions on how to manage threads, users, and message flows.

---

## 1. Terminology Glossary

| Term | Definition | Context / Invariant |
| :--- | :--- | :--- |
| **User (Participant)** | A human or an AI agent interacting with the system. Each user has their own private local workspace (drafts) and a synced cloud directory (outbox & receipts). | Users only write to their own outboxes; they read from shared threads. |
| **Local Draft** | A private, mutable message in progress. Drafts contain a body file (`body.md`) and any locally copied attachments. They are not visible to other users. | Editable at any time. Located in `drafts/<user_id>/`. |
| **Outbox Package** | A folder containing an immutable message published by a user. Once published, it cannot be modified. Naming scheme: `U<local_id>_<unique_suffix>`. | Located in `users/<user_id>/outbox/`. |
| **Thread (Topic)** | A shared, topic-oriented folder context (e.g., `T_20260627_A1B2`) where distributed messages are collected. Contains a configuration file (`thread.json`) and description (`README.md`). | Located in `threads/`. Can be `OPEN` or `DONE`. |
| **Receipt** | A small JSON file (`<local_id>_receipt.json`) written by the coordinator to the user's receipts folder acknowledging successful distribution. | Located in `users/<user_id>/receipts/`. |
| **Global Coordinator** | The background synchronization engine. It reads registered user outboxes, validates messages, copies them idempotently to target threads, issues receipts, and archives closed threads. | Only one coordinator runs per setup in Version 1.0. |
| **Ledger (SQLite Cache)** | A local SQLite database (`coordinator_ledger.db`) maintained by the coordinator to keep track of already distributed message hashes and keys (`source_user_id + source_local_message_id`). | Rebuildable automatically from the filesystem. |
| **Archive** | A zipped copy of a completed thread (`T_<thread_id>.zip`) stored for long-term records. Live folder is cleaned up once archived. | Located in `archive/`. |
| **Staging** | A temporary directory used by the client library to compile message packages before moving them atomically to the outbox. | Prevents sync managers from reading half-written files. |

---

## 2. End-User Operations Guide

### A. How to Register Users
The coordinator only processes users listed in the registered users configuration:
1.  Locate the text file at: `G:\My Drive\shikibo_test\config\registered_users.txt`
2.  Open the file and add the username of the user (one username per line):
    ```
    agent_reviewer
    human_wayne
    ```
3.  Save the file. On its next scan, the coordinator will monitor these users and dynamically discover their main outboxes and any child role outboxes.

### B. How to Create a New Topic (Thread)
#### Via the WebApp:
1.  Click the **"+ New Thread"** button in the left sidebar.
2.  Fill in the fields:
    *   **Thread ID**: Use a unique alphanumeric ID (e.g., `T_20260627_PLAN`).
    *   **Title / Topic**: A short summary of the topic.
    *   **Description**: A markdown description explaining the context.
3.  Click **"Create"**. A new directory is initialized under `threads/`.

---

### C. How to Compose and Publish Messages
#### Via the WebApp:
1.  Select the target thread from the sidebar. The message composer will appear.
2.  Write your message in the text area (supports Markdown formatting).
3.  *(Optional)* Click **"Attach File"** to add document attachments, images, or audio/video files to your message draft.
4.  Click **"Save Draft"** if you want to continue working on it later.
5.  Click **"Publish Message"**. This compiles the package, moves it atomically into your outbox, and cleans up the local draft.

---

### D. How to Run the Coordinator and Scan Outboxes
Messages published in your outbox are not visible to other users until the coordinator distributes them.
*   **Manual Trigger**: Click the **"Trigger Scan Now"** button in the WebApp footer. The status line will display the results (e.g. *Done. Processed: 1*).
*   **Daemon mode**: Launch the coordinator in timed background service mode using the CLI:
    ```powershell
    .venv\Scripts\python main.py service
    ```

---

### E. How to Close and Archive Topics
When a thread has run its course, it should be archived to clean up active storage:
1.  Select the thread in the WebApp.
2.  Click the **"Mark DONE"** button in the thread header.
3.  On the next coordinator scan (triggered manually or by daemon), the coordinator will compile the entire thread folder into a `.zip` archive under `archive/T_<thread_id>.zip` and remove the active thread folder.
