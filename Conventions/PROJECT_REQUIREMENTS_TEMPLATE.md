# PROJECT_REQUIREMENTS.md (Template)

## 1. Purpose & Scope
- **Purpose**: What problem does this project solve and for whom?
- **Scope (MVP)**: Boundaries of the first release.
  - **Core Features**: Bullet list of must-haves
  - **Limitations/Out of Scope**: Explicit non-goals

## 2. Stakeholders & Actors
- **Stakeholders**: Roles and responsibilities
- **Actors**: End-users or systems interacting with the product

## 3. User Stories
- As a <actor>, I want <capability> so that <goal>.
- Acceptance criteria for each story

## 4. Functional Requirements
- Feature A
  - Description
  - Triggers/Inputs
  - Expected behavior
  - Errors/edge cases

## 5. Non-Functional Requirements
- Performance, scalability, availability
- Security and privacy requirements
- Observability (logs/metrics/alerts)

## 6. Data Model Impact
- Entities/tables affected (reference `codebase_registry.json` and `schema.sql`)
- Enum lists and validation pattern IDs (reference `global_validation_patterns.yaml.md`)

## 7. API & Interfaces
- Endpoints/functions (paths, methods, request/response schemas)
- Permissions (roles/capabilities)

## 8. UI Pages & Blocks
- Pages/blocks (reference `ui_blocks_template.json`)
- State persistence (get_ui_state/set_ui_state)

## 9. Dependencies
- Internal module dependencies (reference `codebase_registry.json`)
- External services/libraries

## 10. Risks, Assumptions, Constraints
- Known risks and mitigations
- Assumptions that may change
- Constraints (legal, compliance, technical)

## 11. Exceptions to Conventions
- Proposed exceptions (reference rule IDs from `CONVENTIONS.json`)
- Rationale, risks, approvals, PR/issue links

## 12. Success Metrics
- KPIs, SLAs, or measurable outcomes for MVP

## 13. Open Questions
- Outstanding decisions and owners