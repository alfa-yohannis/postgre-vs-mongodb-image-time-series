-- ============================================================
-- COMMAND TO RUN THIS SCRIPT:
-- Create the database first (only once):
--   $ sudo -u postgres createdb iot_ts
--
-- Then run:
--   $ sudo -u postgres psql -d iot_ts -f postgre_sensor_frames.sql
-- ============================================================


-- ============================================================
-- ENABLE TIMESCALEDB EXTENSION (SAFE)
-- ============================================================
-- This only enables it in THIS DATABASE.
-- It does NOT drop or reload anything.
-- This is REQUIRED if it's not enabled yet.

CREATE EXTENSION IF NOT EXISTS timescaledb;


-- ============================================================
-- HARD RESET: DROP TABLE ONLY (KEEP EXTENSION)
-- ============================================================

DROP TABLE IF EXISTS sensor_frames CASCADE;


-- ============================================================
-- MAIN TABLE: TIME-SERIES + IMAGE (320x240)
-- ============================================================

CREATE TABLE sensor_frames (
    id          BIGSERIAL    NOT NULL,
    device_id   BIGINT       NOT NULL,
    ts          TIMESTAMPTZ  NOT NULL,
    frame_data  BYTEA        NOT NULL,   -- 320x240 image bytes (JPEG/PNG)
    width       INT          NOT NULL DEFAULT 320,
    height      INT          NOT NULL DEFAULT 240,
    mime_type   TEXT         NOT NULL,   -- 'image/jpeg' or 'image/png'
    created_at  TIMESTAMPTZ  DEFAULT now(),

    -- REQUIRED BY TIMESCALE:
    -- Partition column must be part of a UNIQUE or PRIMARY KEY
    PRIMARY KEY (ts, id)
);


-- ============================================================
-- INDEX FOR TIME-SERIES QUERIES
-- ============================================================

CREATE INDEX idx_sensor_frames_device_ts
ON sensor_frames (device_id, ts);


-- ============================================================
-- CONVERT TO HYPERTABLE (NOW GUARANTEED TO WORK)
-- ============================================================

SELECT create_hypertable('sensor_frames', 'ts', if_not_exists => TRUE);


-- ============================================================
-- TEST INSERT (ONE 320x240 DUMMY IMAGE RECORD)
-- ============================================================

INSERT INTO sensor_frames (
    device_id, ts, frame_data, width, height, mime_type
)
VALUES (
    1,
    now(),
    decode(repeat('FF', 320 * 240 / 2), 'hex'),  -- dummy binary payload
    320,
    240,
    'image/jpeg'
);


-- ============================================================
-- TEST QUERY
-- ============================================================

SELECT
    id,
    device_id,
    ts,
    octet_length(frame_data) AS image_size_bytes,
    width,
    height,
    mime_type
FROM sensor_frames
ORDER BY ts DESC
LIMIT 5;
