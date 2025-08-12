# Step 2: Pre-Review Decomposition (Atomic Statements)

## Approach

* Each section and sub-rule is broken into **atomic** statements and labeled for reference.
* This step enables precise cross-referencing for the later redundancy, overlap, and logic checks.

---

## **Decomposition Table**

```
ID  Atomic Rule Statement 

1.1   All audit tables must reside in `audit` schema.
1.2   Audit tables must be protected against modification after insert (REVOKE UPDATE/DELETE).
1.3   For Postgres 12+, enable RLS and policy for insert-only audit logs.
1.4   No application/migration code may alter, update, or delete audit records.
1.5   Audit schema changes must be reviewed/tested for immutability.
2.1   All cross-table references must use explicit FOREIGN KEY constraints.
2.2   Every FOREIGN KEY must specify ON DELETE/ON UPDATE policy.
2.3   All FK columns must have an INDEX.
3.1   Polymorphic link tables must enforce valid (type, id) pairs.
3.2   Use triggers or CI to validate (type, id) pairings.
3.3   Refer to codebase_registry_template.json for relation pattern.
4.1   Unique constraints must be DEFERRABLE INITIALLY IMMEDIATE unless justified.
4.2   Constraints on user/mutable fields must be unique as needed.
5.1   All mutable/business tables must include created_at, updated_at, version.
5.2   Version field must increment on every UPDATE (by app or trigger).
5.3   All module_data.json specs must declare a version field.
5.4   CI/tests must verify all business models/tables have version column and it increments.
5.5   Any mutable table w/o version requires documented exception per Section 12.
5.6   Static lookup/reference tables are exempt.
6.1   All domain value fields must use explicit ENUM types.
6.2   Enum values must be documented and UI-synced if practical.
6.3   Refer to ui_blocks_template.json for mapping.
7.1   JSONB business data must be validated by CHECK, trigger, or app+test.
7.2   Log/debug fields may have relaxed validation if documented.
7.3   Refer to codebase_registry_template.json/ui_blocks_template.json for validation_method.
8.1   All foreign key columns must have an INDEX.
8.2   All frequent filter/sort/join columns must be indexed.   
8.3   Indexes must be reviewed with every schema update.  
9.1   Each data model must have explicit owner module (see registry template).
9.2   All inter-table relations must be explicit (FK or linking table).  
10.1  Every mutation on business table must emit audit record. 
10.2  Audit coverage enforced by automated tests (CI fails if not present).   
10.3  Refer to codebase_registry_template.json for test description.   
11.1  All constraints, triggers, and RLS policies must have automated tests.  
11.2  All migrations/schema updates must be validated before deployment. 
12.1  Any deviation must be documented (rationale, risk, approval). 
12.2  See exceptions array in both templates.   
13.1  UI actions invoking cross-module logic must declare module_dependency and function_call.  
13.2  Applies to all actions that interact with polymorphic linking or cross-entity relationships.
13.3  All such actions must route through owning module’s API. 
13.4  ui_blocks_template.json must reflect these requirements.    
13.5  CI must ensure all ui_block.json files conform to this. 
13.6  Changes to dependencies must be reviewed for modularity/reuse.
14.1  All DB/table/column/index/constraint names must use snake_case.   
14.2  PK columns named `id`.
14.3  FK columns named `<table>_id`.  
14.4  Indexes: `idx_<table>_<column>`.
14.5  Constraints: PK, FK, UQ, CK prefixes as specified.  
14.6  Filenames: lowercase, underscores.   
14.7  Deviation must be documented/approved.    
14.8  Python: Class names PascalCase, file/modules snake_case, functions/vars snake_case.  
14.9  DB models use direct PascalCase mapping.  
14.10 Non-compliant artifacts must be listed in exceptions.    
15.1  All schema changes by hand-written SQL on DB.  
15.2  After change, canonical schema dump as schema.sql.  
15.3  schema.sql committed after every change.  
15.4  No tool-managed migrations during MVP.    
15.5  schema.sql is authoritative for code/specs.    
15.6  Manual destructive ops require backup.    
15.7  Never edit schema.sql directly; update DB then export.   
15.8  If/when migration tool is adopted, update and retro-doc migrations.
16.1  Every UI pane/block with state must implement get_ui_state/set_ui_state. 
16.2  These hooks must serialize/restore all UI configuration. 
16.3  All UI specs must document state hook implementations.   
16.4  Tests/CI must verify required hooks. 
16.5  Omission must be justified in exceptions. 
17.1  codebase_registry.json is authoritative registry.  
17.2  All modules/interfaces/deps registered before implementation/spec. 
17.3  Registry and codebase/specs must be strictly synced.
17.4  CI/code review must check for drift. 
17.5  Major registry changes require approval/documented rationale. 
18.1  All DB-interacting tests must run in rollbacked transaction.  
18.2  Use fixture/context manager for test DB isolation.  
18.3  Tests must be independently repeatable/idempotent.  
18.4  Exceptions for integration/migration tests must be documented.
18.5  Persistent tests must be marked/run separately.
19.1  Version column on business tables must increment on UPDATE.   
19.2  Enforcement method must be documented in module spec.    
19.3  CI/tests verify version increments.  
19.4  Exceptions must be documented/approved.   
20.1  Env config files with secrets must be excluded from VCS. 
20.2  Production secrets/creds never stored/repo/shared plaintext.  
20.3  Local .env allowed, but never committed.  
20.4  Exposed secrets must be rotated and incident documented. 
20.5  Deviations must be approved/justified.    
```

---
