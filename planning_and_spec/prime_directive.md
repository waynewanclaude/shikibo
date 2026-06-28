# Prime Directive: User Folder & File Protections

This document defines the strict safety directives that all code, scripts, test cases, and AI actions in this repository must adhere to.

## Core Mandates

### 1. Preservation of User-Created Directories
No ad hoc script, test suite, or core application code is allowed to destroy, delete, rename, or modify user-created root directories (e.g., the root transport directory `G:\My Drive\itracker_test` or the repository root).

### 2. Strict Targeted Cleanup
If a testing script or verification suite needs to clear previous state before a run, it must do so by targeting only specific, temporary, test-generated sub-directories and files. It must never perform blanket recursive deletions on parent user folders.
*   **Approved Cleanup Targets**: `threads/T_<test_id>`, `users/<test_user_id>`, `drafts/<test_user_id>`, `coordinator/coordinator_ledger.db`
*   **Prohibited Cleanup Targets**: Any parent directory like `<root_dir>/`, `config/`, or shared workspace volumes.

### 3. Safe Deletions Invariants
Core system file deletions are limited strictly to:
*   Deleting a mutable local draft folder **only after** it has been successfully staged, verified, and atomically published to the outbox.
*   Removing a live thread folder **only after** it has been successfully zipped and written to the `archive/` directory, and the archive's size and existence are verified.
