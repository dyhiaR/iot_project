-- =========================
-- Tables (si besoin)
-- =========================
CREATE TABLE IF NOT EXISTS users (
  id SERIAL PRIMARY KEY,
  nom TEXT NOT NULL,
  prenom TEXT NOT NULL,
  email TEXT NOT NULL UNIQUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS sessions (
  id SERIAL PRIMARY KEY,
  user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  start_time TIMESTAMPTZ NOT NULL DEFAULT now(),
  end_time TIMESTAMPTZ,
  status TEXT NOT NULL DEFAULT 'stopped' CHECK (status IN ('running','stopped','aborted'))
);

CREATE TABLE IF NOT EXISTS gps_points (
  id SERIAL PRIMARY KEY,
  session_id INT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  ts TIMESTAMPTZ NOT NULL,
  lat DOUBLE PRECISION NOT NULL,
  lon DOUBLE PRECISION NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sessions_user_time ON sessions(user_id, start_time DESC);
CREATE INDEX IF NOT EXISTS idx_gps_points_session_ts ON gps_points(session_id, ts);

-- =========================

INSERT INTO users (id, nom, prenom, email) VALUES
  (1, 'user', 'test', 'test@gmail.com'),
  (2,  'dyhia', 'sarah', 'dyhia@gmail.com')
ON CONFLICT (email) DO NOTHING;

-- ==================-- =========================

-- ---------- USER 1 : 4 sessions ----------
WITH s AS (
  INSERT INTO sessions (user_id, start_time, end_time, status)
  VALUES
    (1, '2026-02-01 09:00:00+00', '2026-02-01 09:06:00+00', 'stopped')
  RETURNING id
)
INSERT INTO gps_points(session_id, ts, lat, lon)
SELECT id, ts, lat, lon FROM (
  SELECT (SELECT id FROM s) AS id,
         unnest(ARRAY[
           '2026-02-01 09:00:00+00'::timestamptz,
           '2026-02-01 09:01:00+00',
           '2026-02-01 09:02:00+00',
           '2026-02-01 09:03:00+00',
           '2026-02-01 09:04:00+00',
           '2026-02-01 09:05:00+00',
           '2026-02-01 09:06:00+00'
         ]) AS ts,
         unnest(ARRAY[48.85710,48.85735,48.85762,48.85788,48.85810,48.85834,48.85855]) AS lat,
         unnest(ARRAY[2.35160,2.35195,2.35225,2.35255,2.35285,2.35315,2.35345]) AS lon
) q;

WITH s AS (
  INSERT INTO sessions (user_id, start_time, end_time, status)
  VALUES
    (1, '2026-02-03 18:10:00+00', '2026-02-03 18:18:00+00', 'stopped')
  RETURNING id
)
INSERT INTO gps_points(session_id, ts, lat, lon)
SELECT id, ts, lat, lon FROM (
  SELECT (SELECT id FROM s) AS id,
         unnest(ARRAY[
           '2026-02-03 18:10:00+00'::timestamptz,
           '2026-02-03 18:11:00+00',
           '2026-02-03 18:12:00+00',
           '2026-02-03 18:13:00+00',
           '2026-02-03 18:14:00+00',
           '2026-02-03 18:15:00+00',
           '2026-02-03 18:16:00+00',
           '2026-02-03 18:17:00+00',
           '2026-02-03 18:18:00+00'
         ]) AS ts,
         unnest(ARRAY[48.85620,48.85628,48.85638,48.85650,48.85663,48.85678,48.85692,48.85705,48.85718]) AS lat,
         unnest(ARRAY[2.35480,2.35455,2.35430,2.35405,2.35380,2.35355,2.35330,2.35305,2.35280]) AS lon
) q;

WITH s AS (
  INSERT INTO sessions (user_id, start_time, end_time, status)
  VALUES
    (1, '2026-02-06 07:30:00+00', '2026-02-06 07:37:00+00', 'stopped')
  RETURNING id
)
INSERT INTO gps_points(session_id, ts, lat, lon)
SELECT id, ts, lat, lon FROM (
  SELECT (SELECT id FROM s) AS id,
         unnest(ARRAY[
           '2026-02-06 07:30:00+00'::timestamptz,
           '2026-02-06 07:31:00+00',
           '2026-02-06 07:32:00+00',
           '2026-02-06 07:33:00+00',
           '2026-02-06 07:34:00+00',
           '2026-02-06 07:35:00+00',
           '2026-02-06 07:36:00+00',
           '2026-02-06 07:37:00+00'
         ]) AS ts,
         unnest(ARRAY[48.86010,48.86002,48.85995,48.85990,48.85988,48.85990,48.85996,48.86005]) AS lat,
         unnest(ARRAY[2.34010,2.34035,2.34062,2.34090,2.34120,2.34148,2.34175,2.34200]) AS lon
) q;

WITH s AS (
  INSERT INTO sessions (user_id, start_time, end_time, status)
  VALUES
    (1, '2026-02-08 12:00:00+00', '2026-02-08 12:05:00+00', 'stopped')
  RETURNING id
)
INSERT INTO gps_points(session_id, ts, lat, lon)
SELECT id, ts, lat, lon FROM (
  SELECT (SELECT id FROM s) AS id,
         unnest(ARRAY[
           '2026-02-08 12:00:00+00'::timestamptz,
           '2026-02-08 12:01:00+00',
           '2026-02-08 12:02:00+00',
           '2026-02-08 12:03:00+00',
           '2026-02-08 12:04:00+00',
           '2026-02-08 12:05:00+00'
         ]) AS ts,
         unnest(ARRAY[48.85390,48.85410,48.85428,48.85440,48.85448,48.85455]) AS lat,
         unnest(ARRAY[2.34720,2.34745,2.34770,2.34795,2.34820,2.34845]) AS lon
) q;

-- ---------- USER 2 : 3 sessions ----------
WITH s AS (
  INSERT INTO sessions (user_id, start_time, end_time, status)
  VALUES
    (2, '2026-02-02 10:15:00+00', '2026-02-02 10:22:00+00', 'stopped')
  RETURNING id
)
INSERT INTO gps_points(session_id, ts, lat, lon)
SELECT id, ts, lat, lon FROM (
  SELECT (SELECT id FROM s) AS id,
         unnest(ARRAY[
           '2026-02-02 10:15:00+00'::timestamptz,
           '2026-02-02 10:16:00+00',
           '2026-02-02 10:17:00+00',
           '2026-02-02 10:18:00+00',
           '2026-02-02 10:19:00+00',
           '2026-02-02 10:20:00+00',
           '2026-02-02 10:21:00+00',
           '2026-02-02 10:22:00+00'
         ]) AS ts,
         unnest(ARRAY[48.86530,48.86510,48.86492,48.86475,48.86460,48.86445,48.86430,48.86415]) AS lat,
         unnest(ARRAY[2.35720,2.35700,2.35680,2.35655,2.35630,2.35605,2.35580,2.35555]) AS lon
) q;

WITH s AS (
  INSERT INTO sessions (user_id, start_time, end_time, status)
  VALUES
    (2, '2026-02-05 19:40:00+00', '2026-02-05 19:47:00+00', 'stopped')
  RETURNING id
)
INSERT INTO gps_points(session_id, ts, lat, lon)
SELECT id, ts, lat, lon FROM (
  SELECT (SELECT id FROM s) AS id,
         unnest(ARRAY[
           '2026-02-05 19:40:00+00'::timestamptz,
           '2026-02-05 19:41:00+00',
           '2026-02-05 19:42:00+00',
           '2026-02-05 19:43:00+00',
           '2026-02-05 19:44:00+00',
           '2026-02-05 19:45:00+00',
           '2026-02-05 19:46:00+00',
           '2026-02-05 19:47:00+00'
         ]) AS ts,
         unnest(ARRAY[48.85080,48.85100,48.85120,48.85138,48.85155,48.85170,48.85182,48.85195]) AS lat,
         unnest(ARRAY[2.37110,2.37085,2.37060,2.37035,2.37010,2.36985,2.36960,2.36935]) AS lon
) q;

WITH s AS (
  INSERT INTO sessions (user_id, start_time, end_time, status)
  VALUES
    (2, '2026-02-09 06:55:00+00', '2026-02-09 07:01:00+00', 'stopped')
  RETURNING id
)
INSERT INTO gps_points(session_id, ts, lat, lon)
SELECT id, ts, lat, lon FROM (
  SELECT (SELECT id FROM s) AS id,
         unnest(ARRAY[
           '2026-02-09 06:55:00+00'::timestamptz,
           '2026-02-09 06:56:00+00',
           '2026-02-09 06:57:00+00',
           '2026-02-09 06:58:00+00',
           '2026-02-09 06:59:00+00',
           '2026-02-09 07:00:00+00',
           '2026-02-09 07:01:00+00'
         ]) AS ts,
         unnest(ARRAY[48.85890,48.85875,48.85862,48.85850,48.85838,48.85828,48.85820]) AS lat,
         unnest(ARRAY[2.33680,2.33695,2.33710,2.33728,2.33745,2.33765,2.33785]) AS lon
) q;