CREATE TABLE IF NOT EXISTS usuarios (
  id SERIAL PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS centros_logisticos (
  id SERIAL PRIMARY KEY,
  company_slug TEXT NOT NULL,
  name TEXT NOT NULL,
  lat DOUBLE PRECISION NOT NULL,
  lon DOUBLE PRECISION NOT NULL,
  active BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS locales (
  id TEXT PRIMARY KEY,
  company_slug TEXT NOT NULL,
  name TEXT NOT NULL,
  city TEXT,
  lat DOUBLE PRECISION NOT NULL,
  lon DOUBLE PRECISION NOT NULL,
  rank INT,
  venta_por_dia NUMERIC(14,2),
  active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS rutas (
  id SERIAL PRIMARY KEY,
  company_slug TEXT NOT NULL,
  fecha DATE NOT NULL,
  turno TEXT NOT NULL,
  cerrado BOOLEAN DEFAULT FALSE,
  depot_id INT REFERENCES centros_logisticos(id),
  creado_por INT REFERENCES usuarios(id),
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS rutas_detalles (
  id SERIAL PRIMARY KEY,
  ruta_id INT REFERENCES rutas(id) ON DELETE CASCADE,
  orden INT NOT NULL,
  local_id TEXT REFERENCES locales(id),
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_locales_company ON locales(company_slug);
CREATE INDEX IF NOT EXISTS idx_rutas_company_fecha ON rutas(company_slug, fecha);
