PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL CHECK (length(trim(name)) BETWEEN 2 AND 120),
    username TEXT NOT NULL UNIQUE CHECK (length(trim(username)) BETWEEN 3 AND 60),
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'solicitante' CHECK (role IN ('solicitante', 'gestor')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL CHECK (length(trim(title)) BETWEEN 1 AND 120),
    description TEXT NOT NULL CHECK (length(trim(description)) BETWEEN 1 AND 4000),
    category TEXT NOT NULL CHECK (category IN ('TI', 'RH', 'Compras', 'Financeiro', 'Infraestrutura')),
    status TEXT NOT NULL DEFAULT 'Aberto' CHECK (status IN ('Aberto', 'Em Atendimento', 'Concluído')),
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_requests_status ON requests(status);
CREATE INDEX IF NOT EXISTS idx_requests_category ON requests(category);
CREATE INDEX IF NOT EXISTS idx_requests_created_at ON requests(created_at);
CREATE INDEX IF NOT EXISTS idx_requests_user_id ON requests(user_id);
