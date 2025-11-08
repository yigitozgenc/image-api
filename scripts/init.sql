-- Database schema for image frames
-- This file is for reference. Tables are created automatically via SQLAlchemy.

CREATE TABLE IF NOT EXISTS image_frames (
    id SERIAL PRIMARY KEY,
    depth NUMERIC(10, 2) NOT NULL,
    original_data BYTEA NOT NULL,
    resized_data BYTEA NOT NULL,
    metadata JSONB NOT NULL
);

-- Index on depth for efficient range queries
CREATE INDEX IF NOT EXISTS idx_depth_range ON image_frames(depth);

-- Additional index for depth ordering
CREATE INDEX IF NOT EXISTS idx_depth_asc ON image_frames(depth ASC);

