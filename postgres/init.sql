-- 1) Table users
CREATE TABLE IF NOT EXISTS users (
  id SERIAL PRIMARY KEY,
  nom TEXT NOT NULL,
  prenom TEXT NOT NULL,
  email TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS devices (
  id SERIAL PRIMARY KEY,
  user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  role TEXT NOT NULL CHECK (role IN ('gps', 'battery', 'temperature')),
  ipv6 TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (user_id, role)
);

CREATE TABLE IF NOT EXISTS sessions (
  id SERIAL PRIMARY KEY,
  user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  start_time TIMESTAMPTZ NOT NULL DEFAULT now(),
  end_time TIMESTAMPTZ,
  status TEXT NOT NULL DEFAULT 'running' CHECK (status IN ('running', 'stopped'))
);
-- 2) Données de départ (seed)
INSERT INTO users (id, nom, prenom, email) VALUES
  (1, 'Raab',   'Dyhia', 'dyhia.raab@exemple.com'),
  (2, 'Dupont', 'Alice', 'alice.dupont@exemple.com'),
  (3, 'Martin', 'Yanis', 'yanis.martin@exemple.com')
ON CONFLICT (email) DO NOTHING;

INSERT INTO devices (user_id, role, ipv6) VALUES
  (1, 'gps',         NULL),
  (1, 'battery',     NULL),
  (1, 'temperature', NULL),

  (2, 'gps',         NULL),
  (2, 'battery',     NULL),
  (2, 'temperature', NULL),

  (3, 'gps',         NULL),
  (3, 'battery',     NULL),
  (3, 'temperature', NULL)
ON CONFLICT (user_id, role) DO NOTHING;