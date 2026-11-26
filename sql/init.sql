-- sql/init.sql
CREATE TABLE IF NOT EXISTS window_counts (
    window_start TIMESTAMP NOT NULL,
    window_end TIMESTAMP NOT NULL,
    camera_id VARCHAR(50) NOT NULL,
    cls VARCHAR(50) NOT NULL,
    vehicles INT NOT NULL DEFAULT 0,
    avg_conf REAL,
    PRIMARY KEY (window_start, camera_id, cls)
);