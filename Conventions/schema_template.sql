-- ==============================================
-- comprehensive_schema_template.sql
-- SQL template following project conventions and schema structure
-- ==============================================

-- 1. Enable required extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pgcrypto; -- for gen_random_uuid()

-- 2. Audit schema (db.audit.schema)
CREATE SCHEMA IF NOT EXISTS audit;

-- 3. Common ENUM type definitions (db.constraint.enum)
-- Example:
-- CREATE TYPE {{enum_name}} AS ENUM ({{'value1', 'value2', ...}});

-- 4. Reusable trigger for timestamps and version bump (db.versioning.bump)
CREATE OR REPLACE FUNCTION trigger_{{table_name}}_timestamps_and_version()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at := now();
  NEW.version := OLD.version + 1;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 5. Table creation template with required conventions
-- Replace {{table_name}} and placeholder fields accordingly
CREATE TABLE {{table_name}} (
  -- Primary key
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),                        -- naming.snake_case

  -- Business fields (define your columns here)
  -- column_name data_type [constraints],

  -- Standard audit columns (db.constraint.timestamps)
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),                       -- MUST include
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),                       -- MUST include
  version INTEGER NOT NULL DEFAULT 1,                                  -- MUST include

  -- Reference to user who created/owns record (db.rel.fk)
  created_by UUID REFERENCES users(id) ON DELETE SET NULL,

  -- Unique constraint example (db.constraint.unique)
  CONSTRAINT uq_{{table_name}}_{{unique_field}} UNIQUE ({{unique_field}}) DEFERRABLE INITIALLY IMMEDIATE,

  -- JSONB validation placeholder (db.constraint.jsonb)
  -- Replace {{jsonb_field}} with your JSONB column name
  CONSTRAINT ck_{{table_name}}_{{jsonb_field}}_jsonb_valid CHECK (jsonb_typeof({{jsonb_field}}) = 'object')
);

-- 6. Attach trigger for update operations
CREATE TRIGGER trg_{{table_name}}_timestamps_and_version
BEFORE UPDATE ON {{table_name}}
FOR EACH ROW
EXECUTE FUNCTION trigger_{{table_name}}_timestamps_and_version();

-- 7. Index definitions (db.index.fk_and_query)
-- Create indexes for each FOREIGN KEY and frequent query columns
-- Example:
-- CREATE INDEX idx_{{table_name}}_{{column_name}} ON {{table_name}}({{column_name}});

-- 8. Audit table template (db.audit.immutability)
-- Copy and adapt for each business table if audit logs are required
CREATE TABLE audit.{{table_name}}_audit (
  operation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  table_name TEXT NOT NULL,
  operation CHAR(1) NOT NULL CHECK (operation IN ('I','U','D')),
  record_id UUID NOT NULL,
  changed_data JSONB,
  performed_by UUID REFERENCES users(id),
  performed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 9. Polymorphic link table template (db.rel.polymorphic)
-- Define for linking multiple entity types via a single table
CREATE TABLE {{link_table_name}} (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_type TEXT NOT NULL,
  owner_id UUID NOT NULL,
  item_type TEXT NOT NULL,
  item_id UUID NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by UUID REFERENCES users(id),

  -- Prevent duplicate links (db.constraint.unique)
  CONSTRAINT uq_{{link_table_name}}_link UNIQUE (owner_type, owner_id, item_type, item_id) DEFERRABLE INITIALLY IMMEDIATE
);

-- 10. Additional index templates
-- CREATE INDEX idx_{{link_table_name}}_owner ON {{link_table_name}}(owner_type, owner_id);
-- CREATE INDEX idx_{{link_table_name}}_item ON {{link_table_name}}(item_type, item_id);

-- 11. Notes:
-- • Use snake_case for all identifiers (naming.snake_case).
-- • Document any deviations as exceptions (meta.exception.doc).
-- • Ensure ENUM values remain in sync across DB, code, and UI (db.constraint.enum_sync).
-- • Validate JSONB fields via CHECK, trigger, or tested application logic (db.constraint.jsonb).
-- • All schema changes MUST be hand-written and exported to schema.sql (db.migration.manual).
-- • Backup database prior to destructive operations (db.migration.backup).
