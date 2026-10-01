from __future__ import annotations

import hmac
import os
import secrets
import sqlite3
from datetime import date, datetime, timezone
from functools import wraps
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, g, jsonify, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
DATABASE = Path(os.getenv("DATABASE_PATH", BASE_DIR / "instance" / "solicitacoes.db"))
CATEGORIES = ("TI", "RH", "Compras", "Financeiro", "Infraestrutura")
STATUSES = ("Aberto", "Em Atendimento", "Concluído")

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.getenv("SECRET_KEY", "dev-only-change-this-secret"),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.getenv("COOKIE_SECURE", "false").lower() == "true",
    MAX_CONTENT_LENGTH=64 * 1024,
)


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        DATABASE.parent.mkdir(parents=True, exist_ok=True)
        g.db = sqlite3.connect(DATABASE, timeout=10)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_error=None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    DATABASE.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DATABASE)
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript((BASE_DIR / "database" / "schema.sql").read_text(encoding="utf-8"))
    count = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if count == 0:
        db.executemany(
            "INSERT INTO users (name, username, password_hash, role) VALUES (?, ?, ?, ?)",
            [
                ("Marina Costa", "marina", generate_password_hash(os.getenv("DEMO_USER_PASSWORD", "Marina@2026")), "solicitante"),
                ("Rafael Lima", "gestor", generate_password_hash(os.getenv("DEMO_ADMIN_PASSWORD", "Gestor@2026")), "gestor"),
            ],
        )
    db.commit()
    db.close()


def api_error(message: str, status: int = 400):
    return jsonify({"error": message}), status


def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return get_db().execute("SELECT id, name, username, role FROM users WHERE id = ?", (user_id,)).fetchone()


def login_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        user = current_user()
        if user is None:
            return api_error("Faça login para continuar.", 401)
        g.user = user
        return fn(*args, **kwargs)
    return wrapped


def csrf_protected(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        sent = request.headers.get("X-CSRF-Token", "")
        expected = session.get("csrf_token", "")
        if not expected or not hmac.compare_digest(sent, expected):
            return api_error("A sessão expirou. Atualize a página e tente novamente.", 403)
        return fn(*args, **kwargs)
    return wrapped


def request_payload():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None, "Envie os dados em formato JSON."
    title = str(data.get("title", "")).strip()
    description = str(data.get("description", "")).strip()
    category = str(data.get("category", "")).strip()
    if not title or len(title) > 120:
        return None, "O título é obrigatório e deve ter até 120 caracteres."
    if not description or len(description) > 4000:
        return None, "A descrição é obrigatória e deve ter até 4.000 caracteres."
    if category not in CATEGORIES:
        return None, "Selecione uma categoria válida."
    return {"title": title, "description": description, "category": category}, None


def row_to_dict(row):
    return dict(row) if row else None


@app.get("/")
def index():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return render_template("index.html", csrf_token=session["csrf_token"])


@app.get("/api/me")
def me():
    user = current_user()
    return jsonify({"user": row_to_dict(user), "csrf_token": session.get("csrf_token")})


@app.post("/api/login")
@csrf_protected
def login():
    data = request.get_json(silent=True) or {}
    username = str(data.get("username", "")).strip().lower()
    password = str(data.get("password", ""))
    row = get_db().execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    if row is None or not check_password_hash(row["password_hash"], password):
        return api_error("Usuário ou senha inválidos.", 401)
    session.clear()
    session["user_id"] = row["id"]
    session["csrf_token"] = secrets.token_urlsafe(32)
    return jsonify({"user": {"id": row["id"], "name": row["name"], "username": row["username"], "role": row["role"]}, "csrf_token": session["csrf_token"]})


@app.post("/api/logout")
@csrf_protected
def logout():
    session.clear()
    return jsonify({"ok": True})


@app.get("/api/dashboard")
@login_required
def dashboard():
    rows = get_db().execute("SELECT status, COUNT(*) AS total FROM requests GROUP BY status").fetchall()
    counts = {status: 0 for status in STATUSES}
    counts.update({row["status"]: row["total"] for row in rows})
    return jsonify({"total": sum(counts.values()), "by_status": counts})


@app.get("/api/requests")
@login_required
def list_requests():
    clauses, values = [], []
    status = request.args.get("status", "").strip()
    category = request.args.get("category", "").strip()
    search = request.args.get("q", "").strip()
    start, end = request.args.get("start", "").strip(), request.args.get("end", "").strip()
    if status:
        if status not in STATUSES:
            return api_error("Status inválido.")
        clauses.append("r.status = ?"); values.append(status)
    if category:
        if category not in CATEGORIES:
            return api_error("Categoria inválida.")
        clauses.append("r.category = ?"); values.append(category)
    if search:
        clauses.append("r.title LIKE ? ESCAPE '\\'"); values.append("%" + search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%")
    for value, operator in ((start, ">="), (end, "<")):
        if value:
            try:
                parsed = date.fromisoformat(value)
                if operator == "<":
                    parsed = date.fromordinal(parsed.toordinal() + 1)
            except ValueError:
                return api_error("Informe um período válido.")
            clauses.append(f"date(r.created_at) {operator} ?"); values.append(parsed.isoformat())
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    rows = get_db().execute(
        "SELECT r.id, r.title, r.description, r.category, r.status, r.created_at, r.updated_at, r.user_id, u.name AS requester "
        "FROM requests r JOIN users u ON u.id = r.user_id" + where + " ORDER BY r.created_at DESC, r.id DESC", values
    ).fetchall()
    return jsonify({"requests": [dict(row) for row in rows]})


@app.post("/api/requests")
@login_required
@csrf_protected
def create_request():
    data, error = request_payload()
    if error:
        return api_error(error)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    db = get_db()
    cur = db.execute(
        "INSERT INTO requests (title, description, category, status, user_id, created_at, updated_at) VALUES (?, ?, ?, 'Aberto', ?, ?, ?)",
        (data["title"], data["description"], data["category"], g.user["id"], now, now),
    )
    db.commit()
    row = db.execute("SELECT r.*, u.name AS requester FROM requests r JOIN users u ON u.id = r.user_id WHERE r.id = ?", (cur.lastrowid,)).fetchone()
    return jsonify({"request": dict(row)}), 201


def find_request(request_id):
    return get_db().execute(
        "SELECT r.*, u.name AS requester FROM requests r JOIN users u ON u.id = r.user_id WHERE r.id = ?", (request_id,)
    ).fetchone()


@app.get("/api/requests/<int:request_id>")
@login_required
def request_detail(request_id):
    row = find_request(request_id)
    if row is None:
        return api_error("Solicitação não encontrada.", 404)
    return jsonify({"request": dict(row)})


@app.patch("/api/requests/<int:request_id>")
@login_required
@csrf_protected
def update_request(request_id):
    row = find_request(request_id)
    if row is None:
        return api_error("Solicitação não encontrada.", 404)
    if row["status"] != "Aberto" or (row["user_id"] != g.user["id"] and g.user["role"] != "gestor"):
        return api_error("Somente o solicitante ou um gestor pode editar uma solicitação aberta.", 403)
    data, error = request_payload()
    if error:
        return api_error(error)
    db = get_db()
    db.execute("UPDATE requests SET title = ?, description = ?, category = ?, updated_at = ? WHERE id = ?",
               (data["title"], data["description"], data["category"], datetime.now(timezone.utc).isoformat(timespec="seconds"), request_id))
    db.commit()
    return jsonify({"request": dict(find_request(request_id))})


@app.delete("/api/requests/<int:request_id>")
@login_required
@csrf_protected
def delete_request(request_id):
    row = find_request(request_id)
    if row is None:
        return api_error("Solicitação não encontrada.", 404)
    if row["status"] != "Aberto" or (row["user_id"] != g.user["id"] and g.user["role"] != "gestor"):
        return api_error("Somente o solicitante ou um gestor pode excluir uma solicitação aberta.", 403)
    get_db().execute("DELETE FROM requests WHERE id = ?", (request_id,))
    get_db().commit()
    return jsonify({"ok": True})


@app.patch("/api/requests/<int:request_id>/status")
@login_required
@csrf_protected
def change_status(request_id):
    if g.user["role"] != "gestor":
        return api_error("Apenas gestores podem alterar o status.", 403)
    row = find_request(request_id)
    if row is None:
        return api_error("Solicitação não encontrada.", 404)
    data = request.get_json(silent=True) or {}
    status = str(data.get("status", "")).strip()
    if status not in STATUSES:
        return api_error("Selecione um status válido.")
    allowed_next = {"Aberto": "Em Atendimento", "Em Atendimento": "Concluído"}
    if allowed_next.get(row["status"]) != status:
        return api_error("A solicitação só pode avançar para a próxima etapa do fluxo.", 409)
    get_db().execute("UPDATE requests SET status = ?, updated_at = ? WHERE id = ?",
                     (status, datetime.now(timezone.utc).isoformat(timespec="seconds"), request_id))
    get_db().commit()
    return jsonify({"request": dict(find_request(request_id))})


@app.errorhandler(413)
def too_large(_error):
    return api_error("A solicitação excede o tamanho permitido.", 413)


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=os.getenv("FLASK_DEBUG", "false").lower() == "true")
