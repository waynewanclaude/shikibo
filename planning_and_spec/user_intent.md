# USER_INTENT SPEC: Distributed ThreadMail System

## Part 1 — Main Purpose, Setup Constraints, and Design Reasoning

### 1.1 Main Purpose
The system is a low-cost, cloud-folder-based coordination system for humans and AI agents.
Its purpose is to let multiple humans and AI agents coordinate work through durable, topic-oriented message threads without requiring:
*   Public IP addresses
*   DDNS
*   VPN
*   Hosted server
*   Hosted database
*   Cloud provider APIs
*   Realtime delivery
*   High-frequency polling
*   Chat-style instant messaging

The system behaves more like a delayed mail-sorting system than a chat application.
Each participant publishes messages into its own controlled outbox. A single global coordinator later distributes those messages into thread folders. Once messages are distributed into a thread, other participants can read and respond.

The system is intended for low-volume coordination, not high-throughput messaging.

### 1.2 Core Communication Model
The system uses a cloud-synced filesystem folder as the shared transport layer.
The cloud provider may be:
*   Google Drive
*   OneDrive
*   iCloud Drive
*   Dropbox
*   Syncthing
*   Local shared folder
*   Another filesystem-like sync provider

The system must not depend on provider-specific APIs. All interaction with shared storage should happen through ordinary filesystem operations:
*   List folder
*   Read file
*   Write new file
*   Copy folder
*   Move folder
*   Rename staging folder into final folder
*   Optionally watch local filesystem changes

The cloud folder is not a database. It is a durable mailbox and filing cabinet.

### 1.3 Main Architectural Concept
The system has four major logical areas:
1.  **Local Drafts**: Local-only, editable, private.
2.  **Per-User Cloud Outbox**: Immutable package written by the local service (`PUBLISHED_TO_OUTBOX`).
3.  **Global Coordinator Distribution**: Coordinator copies the package into the target thread folders (`DISTRIBUTED_TO_THREAD`).
4.  **Thread Folders & Receipts**: The coordinator writes a receipt for the source user (`ACKED`). When a thread is mature, it is archived (`ARCHIVED`).

### 1.4 User Concept
A User may be a human, an AI agent, or a local automated process.
A User is not necessarily the same thing as a machine. Multiple Users may exist on the same machine.
Each User has:
*   Its own local draft area
*   Its own cloud-visible outbox
*   Its own local message counter
*   Its own receipts folder

Each User is responsible for assigning its own local message IDs. Since each User writes only into its own outbox, no distributed local-message-ID conflict exists.

### 1.5 Outbox Concept
Each User has one private cloud-visible outbox.
The outbox is an application-owned queue. Humans and AI agents must not manually edit the outbox folder.
Humans and agents interact with the outbox only through:
*   WebApp UI
*   Local API
*   Python client library
*   JavaScript client library
*   Approved local service

The local service must refuse to overwrite existing outbox packages. Outbox packages are immutable after publishing. If a user wants to revise a message, it must publish a new message package.

### 1.6 Thread Concept
The system is topic/thread-oriented, not private-message-oriented.
A thread is a temporary work context. A thread:
*   Has a unique thread ID
*   Has a topic/title
*   Has a README-like description
*   Remains open for days or weeks
*   Receives distributed messages
*   May contain attachments and multimodal content
*   Is marked DONE when mature
*   Is not reopened after DONE (may be extended by creating a new thread linked to the old thread)

The system should not model chat rooms or direct messages as the primary abstraction.

### 1.7 DONE and Follow-Up Behavior
Threads do not reopen. If additional work is needed after a thread is DONE, the system creates a new thread that references the old one.
*   *Example*:
    *   `T_20260627_A1B2` = original thread
    *   `T_20260705_C9D3` = follow-up thread, extends `T_20260627_A1B2`

This avoids lifecycle ambiguity and prevents closed records from being mutated.

### 1.8 Multimodal Messages
Messages may include:
*   Markdown text
*   Images
*   PDFs
*   Audio / Video
*   CSV / JSON files
*   Arbitrary attachments

Large binary content should not be embedded directly in JSON metadata. A message package contains:
*   `message.json`: Metadata schema containing protocol fields (schema version, source user/role ID, local ID, target thread ID, content hash, file attachment records, and a `mentions` list of user/role identities automatically extracted from `@mentions` in the markdown body).
*   `body.md`: Markdown text content.
*   `attachments/`: Directory of copy-staged binary files.

The metadata includes MIME/media type information so the WebApp can render or play attachments with suitable controls.

### 1.9 Global Coordinator Concept
The global coordinator is a background distributor. In version 1, there is only one coordinator.
The coordinator:
*   Scans registered User outboxes (ignores unregistered outboxes)
*   Distributes immutable outbox packages into target thread folders
*   Assigns distributed timestamp and distributed counter
*   Writes receipts
*   Updates indexes periodically
*   Archives DONE threads
*   Maintains a local ledger/cache
*   Can rebuild state from the filesystem

The coordinator is not required for Users to publish to their outboxes. If the coordinator is down, Users can still draft locally and publish immutable outbox messages. When the coordinator returns, it catches up.

### 1.10 Message Ordering
There are two different orders:
1.  **User-local order**: Assigned by each User in its own outbox.
2.  **Thread distribution order**: Assigned by the coordinator when distributing into a thread.

The official thread-visible order is the coordinator distribution order.
Client device clocks may not be synchronized. Therefore, client timestamps must not be used as the primary global ordering source.
The distributed timestamp means: **the time the coordinator first observed and accepted a stable outbox package**.
The final thread message filename includes: `<distributed_timestamp>_<coordinator_counter>_<source_user_id>_<source_local_message_id>`.
*   *Example*: `20260627T161501Z_000001_agent_reviewer_U000017`

The counter resolves same-timestamp collisions.

### 1.11 No-Loss Requirement
No message should be lost. The system assumes sync delays, duplicate sync events, slow file writes, missed watcher events, and coordinator crashes.
Therefore:
*   Outbox packages are immutable and not deleted by Users.
*   Coordinator processes idempotently (deduplicates based on `source_user_id + source_local_message_id`).
*   Receipts are written after distribution.
*   Recovery can rebuild entirely from outboxes and thread folders.
*   Periodic scans are the correctness path (watchers are just an optimization).

### 1.12 Cloud-Friendliness Requirement
The system should avoid abusing cloud storage. It should avoid:
*   Frequent heartbeats
*   Tight polling loops
*   Lock-file churn
*   Repeated overwrites
*   Editing the same global index constantly

Preferred behavior:
*   Append-only outbox packages
*   Batched coordinator scans and distribution
*   Periodic index refresh
*   Low-frequency cleanup
*   Archival of closed threads

### 1.13 Version-1 Scope
*   **Included**: One global coordinator, manual registered-users config (`registered_users.txt`), local WebApp, local client service, Python client library, filesystem-based storage, local drafts, immutable outbox packages, thread folders, receipts, archive support.
*   **Excluded**: Redundant coordinators, leader election, shared-secret coordinator negotiation, provider-specific Drive/iCloud APIs, realtime messaging, public server, hosted database, mobile app.

---

## Part 2 — WebApp User Intent

### 2.1 WebApp Purpose
The WebApp is the human-facing local interface. It allows humans to:
*   Read distributed threads
*   Create and edit local drafts
*   Attach files
*   Publish immutable messages to their own User outbox
*   View pending outbox messages
*   View receipts
*   Request new threads
*   Mark or request DONE
*   Browse archived threads
*   Inspect attachments and multimodal content

The WebApp is a standalone local application (Python local app serving a browser UI).

### 2.2 WebApp Operating Model
The WebApp runs locally and is configured with:
*   `user_id` and `display_name`
*   `local_draft_root`, `outbox_root`, `receipt_root`, `thread_root`, `index_root`, `archive_root`

The WebApp owns the User's local draft workflow and outbox publishing workflow. It must not require cloud provider APIs and must not assume the global coordinator is always online.

### 2.3 Human Draft Behavior
Human users should never manually write into their outbox. The WebApp provides a local draft area where users can repeatedly save, revise, attach, and preview. Drafts are local, private, mutable, and not processed by the coordinator until Published.

### 2.4 Publish Behavior
When the user publishes a draft, the WebApp creates a new immutable outbox package. The WebApp must:
1.  Generate a new User-local message ID.
2.  Create a staging package outside the final outbox location.
3.  Copy `message.json`, `body.md`, and attachments into staging.
4.  Validate that the final outbox folder does not already exist.
5.  Move or rename staging into the outbox as the final package (refusing overwrite).
6.  Mark the draft as submitted.
7.  Keep the draft or submitted snapshot for local recovery.

### 2.5 WebApp Read Behavior
The WebApp reads messages only from distributed thread folders. A message in a User outbox is not considered readable by other Users until the coordinator distributes it into the target thread. The WebApp may show the local User's pending outbox messages separately but must label them as pending/not distributed.

### 2.6 WebApp Thread View
The WebApp should provide:
*   Active Threads list (with title/topic/description search)
*   Thread detail view
*   Message timeline
*   Message composer
*   Attachment panel
*   Pending outbox panel
*   Receipts/status panel
*   Archive browser

### 2.7 WebApp Multimodal Rendering
The WebApp must display or play message attachments according to media type:
*   `image/*`: Show image preview
*   `audio/*`: Show audio player
*   `video/*`: Show video player
*   `application/pdf`: Show open/download button or embedded PDF viewer
*   `text/plain`: Show text preview
*   `text/markdown`: Render Markdown preview
*   `text/csv`: Show table preview if practical, otherwise download button
*   `application/json`: Show structured preview if practical

---

## Part 3 — Global Coordinator User Intent

### 3.1 Coordinator Purpose
The global coordinator is the only component that distributes User outbox messages into readable thread folders. It acts as a slow, durable mail sorter.

### 3.2 Coordinator Input & Output
*   **Inputs**:
    *   `config/registered_users.txt` (simple text file containing one registered top-level username per line)
    *   `users/<user_id>/outbox/`
    *   `threads/`
    *   `index/`
    *   `archive/`
*   **Outputs**:
    *   `threads/<thread_id>/messages/`
    *   `users/<user_id>/receipts/`
    *   `index/`
    *   `archive/`
    *   Coordinator state / ledger
    *   `coordinator/dead_letter/`

### 3.3 Coordinator Distribution Behavior
1.  Detect package and verify it is stable.
2.  Validate package structure and read source User ID and local message ID.
3.  Check whether that source identity was already distributed (deduplication).
4.  Validate target thread exists and is open.
5.  Assign distributed timestamp and distributed counter.
6.  Copy package into target thread message folder.
7.  Write receipt.
8.  Update ledger/cache.
9.  Optionally move or mark package as processed later.

The coordinator must be idempotent. If the receipt is missing for an already distributed message, it may rewrite the receipt.

### 3.4 Coordinator Ledger
The coordinator may maintain a local SQLite ledger for efficiency. However, the ledger must not be the only truth. The coordinator must be able to rebuild its state from the filesystem by scanning distributed thread messages, outbox packages, receipts, and archive metadata.
The core deduplication key is: `source_user_id + source_local_message_id`.

### 3.5 No-Loss Coordinator Rules
The coordinator must never delete an outbox package before safely distributing it and writing a receipt. The safe order is:
1.  Read outbox package
2.  Copy to thread
3.  Verify copy
4.  Write receipt
5.  Record ledger
6.  (Optional) Mark processed or move later

### 3.6 Dead-Letter Behavior
Invalid packages (malformed JSON, missing body, unknown/closed thread, duplicate source ID) should be moved or copied into dead-letter storage with an error explanation, allowing the coordinator to continue processing other messages.

### 3.7 Archive Behavior
When a thread is DONE, the coordinator archives it into `archive/T_<thread_id>.zip` containing `README.md`, `manifest.json`, `messages/`, and `attachments/`.

---

## Part 4 — Client Library User Intent

### 4.1 Client Library Purpose
The client library provides a common programmatic interface for humans, AI agents, scripts, and the WebApp. It hides filesystem details, enforces protocol rules, and supports:
*   Draft creation, editing, and deletion
*   Attachment management
*   Message package creation and ID assignment
*   Safe outbox publishing (no overwrite, immutable outbox packages)
*   Thread reading
*   Receipt and pending outbox reading

### 4.2 Storage Abstraction
The client library should depend on a storage abstraction (`list`, `read`, `write_new`, `copy_tree`, `rename_or_finalize`, `exists`, `stat`) and should not know whether storage is Google Drive, Dropbox, or local disk. No cloud API is required.

### 4.3 Key Client Invariant
*   Drafts are mutable.
*   Outbox packages are immutable.
*   Published packages are never overwritten.
*   Distributed thread messages are coordinator-owned.

### 4.4 Rationale for the Draft System
Although drafts are stored locally in the participant's private workspace, the formal draft system provides crucial benefits:
*   **Persistence & Crash Recovery**: Avoids losing progress if the WebApp or user's environment restarts, switches thread focus, or crashes. Draft metadata and text are saved incrementally on disk.
*   **Safe Attachment Staging**: When files are attached, they are immediately copied to the draft folder. This ensures that even if the user edits, moves, or deletes the original source file on their computer before publishing, the message compiles and publishes successfully.
*   **Consistent Client Interface**: Aligns programmatic inputs from humans (via UI) and AI agents (via code) into a unified workspace flow (`create_draft` -> `update_draft_body` -> `publish_draft`).
*   **Atomic Outbox Staging**: Provides a structured container (`draft.json`, `body.md`, and `attachments/` folder) that can be easily validated, finalized, and atomically renamed/moved into the shared cloud outbox.

### 4.5 Team Scaling & Deployment Philosophy
To keep the application code simple, lightweight, and robust, `shikibo` leverages a scale-free architecture:
*   **Small Teams**: Can be run entirely on a shared local directory (fast, private, and local-only).
*   **Medium Teams**: Can be run on a shared network drive (local intranet).
*   **Large/Distributed Teams**: Can be run on a shared cloud storage folder (Google Drive, Dropbox, OneDrive, iCloud, Syncthing) for global, serverless synchronization.
*   **OS-Native Security Delegation**: The platform does not implement complex application-level security sandboxing. Instead, the `user/role` subfolder layout (`users/<user_id>/<role>/`) allows the platform to delegate permission and write restrictions directly to the underlying Operating System's native file security (POSIX permissions or NTFS ACLs).

