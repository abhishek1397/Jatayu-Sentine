-- sql/create_view.sql
-- This view ensures that every 10-second window has a row for every class, 
-- even if no vehicles were detected (filling gaps with 0).

CREATE OR REPLACE VIEW window_counts_filled AS
WITH RECURSIVE
  -- 1. Get the global min and max time bounds
  time_bounds AS (
      SELECT COALESCE(MIN(window_start), date_trunc('minute', NOW())) AS min_t,
             COALESCE(MAX(window_start), date_trunc('minute', NOW())) AS max_t
      FROM window_counts
  ),
  -- 2. Generate a continuous series of 10-second intervals
  time_series AS (
      SELECT min_t AS window_start FROM time_bounds
      UNION ALL
      SELECT window_start + INTERVAL '10 seconds'
      FROM time_series, time_bounds
      WHERE window_start < max_t
  ),
  -- 3. Hardcode the 10 classes (or extract distinct from table)
  classes(cls) AS (
      VALUES ('auto_rickshaw'), ('e_rickshaw'), ('cycle_rickshaw'), 
             ('tractor_trolley'), ('motorcycle'), ('car'), 
             ('bus'), ('truck'), ('bicycle'), ('pedestrian')
  ),
  -- 4. Get distinct camera_ids
  cameras AS (
      SELECT DISTINCT camera_id FROM window_counts
  ),
  -- 5. Cross join to create the perfect grid of Time x Camera x Class
  grid AS (
      SELECT t.window_start, c.camera_id, cl.cls
      FROM time_series t
      CROSS JOIN cameras c
      CROSS JOIN classes cl
  )
-- 6. Left join the grid with our actual data
SELECT 
    g.window_start,
    g.window_start + INTERVAL '10 seconds' AS window_end,
    g.camera_id,
    g.cls,
    COALESCE(w.vehicles, 0) AS vehicles,
    COALESCE(w.avg_conf, 0.0) AS avg_conf
FROM grid g
LEFT JOIN window_counts w 
    ON g.window_start = w.window_start 
    AND g.camera_id = w.camera_id 
    AND g.cls = w.cls;