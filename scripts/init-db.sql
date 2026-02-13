-- =============================================================================
-- PostgreSQL Initialization Script
-- Enables required extensions for TimescaleDB + pgvector
-- =============================================================================

-- Enable TimescaleDB
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Enable pgvector for RAG embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable uuid-ossp for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pg_trgm for text search
CREATE EXTENSION IF NOT EXISTS pg_trgm;
