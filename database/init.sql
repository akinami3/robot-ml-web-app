-- Initialize Robot ML Database
-- This file is executed automatically when PostgreSQL container starts

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Set timezone
SET timezone = 'UTC';

-- Create custom types
DO $$ BEGIN
    CREATE TYPE recording_status AS ENUM ('recording', 'paused', 'completed', 'discarded');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE training_status AS ENUM ('pending', 'running', 'paused', 'completed', 'failed');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE robot_ml_db TO robot_user;

-- Create initial schema (tables will be created by Alembic migrations)
\echo 'Database initialized successfully'
