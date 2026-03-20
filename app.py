import os
import csv
import io
import html
import hashlib

from fastapi import FastAPI, Form, UploadFile, File, Request
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from openpyxl import Workbook
import psycopg2

app = FastAPI()

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
SECRET_KEY = os.getenv("SECRET_KEY", "cambia-esto-en-render")
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

if not DATABASE_URL:
    raise RuntimeError("Falta la variable de entorno DATABASE_URL")

SESSION_COOKIE = "draft_session"


def hash_text(value: str) -> str:
    return hashlib.sha256((value + SECRET_KEY).encode("utf-8")).hexdigest()


def get_conn():
    return psycopg2.connect(DATABASE_URL)


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS players (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            team TEXT,
            position TEXT,
            status TEXT DEFAULT 'Disponible',
            notes TEXT DEFAULT ''
        )
    """)

    conn.commit()

    cur.execute("SELECT id FROM users WHERE username = %s", (ADMIN_USER,))
    user = cur.fetchone()

    if user:
        cur.execute(
            "UPDATE users SET password_hash = %s, is_admin = TRUE WHERE username = %s",
            (hash_text(ADMIN_PASSWORD), ADMIN_USER)
        )
    else:
        cur.execute(
            "INSERT INTO users (username, password_hash, is_admin) VALUES (%s, %s, %s)",
            (ADMIN_USER, hash_text(ADMIN_PASSWORD), True)
        )

    conn.commit()
    cur.close()
    conn.close()


init_db()

CSS = """
<style>
    * { box-sizing: border-box; }
    body {
        font-family: Arial, sans-serif;
        background: linear-gradient(180deg, #eef3f9 0%, #f8fafc 100%);
        margin: 0;
        padding: 24px;
        color: #1f2937;
    }
    .container { max-width: 1360px; margin: 0 auto; }
    .card {
        background: white;
        border-radius: 18px;
        padding: 22px;
        box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
        margin-bottom: 20px;
        border: 1px solid #e5e7eb;
    }
    .login-wrap { max-width: 420px; margin: 80px auto; }
    h1, h2, h3 { margin-top: 0; }
    h1 { font-size: 34px; margin-bottom: 6px; }
    .grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 12px;
        align-items: end;
    }
    .grid-2 {
        display: grid;
        grid-template-columns: 2fr 1fr;
        gap: 20px;
    }
    label {
        display: block;
        font-size: 14px;
        margin-bottom: 6px;
        font-weight: bold;
    }
    input, select, textarea, button {
        width: 100%;
        padding: 11px 12px;
        border: 1px solid #cbd5e1;
        border-radius: 10px;
        font-size: 14px;
    }
    textarea { min-height: 100px; resize: vertical; }
    input:focus, select:focus, textarea:focus {
        outline: none;
        border-color: #3b82f6;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.12);
    }
    button, .btn, a.btn {
        background: #2563eb;
        color: white;
        border: none;
        cursor: pointer;
        text-decoration: none;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: auto;
        white-space: nowrap;
        font-weight: 600;
    }
    .btn-secondary { background: #475569; }
    .btn-success { background: #16a34a; }
    .btn-danger { background: #dc2626; }
    .btn-warning { background: #d97706; }
    .btn-light { background: #0f766e; }
    .inline-form { display: inline; margin: 0; }
    .actions-toolbar {
        display: flex;
        gap: 6px;
        flex-wrap: nowrap;
        align-items: center;
    }
    .actions-cell { width: 1%; white-space: nowrap; }
    .actions-cell .inline-form, .actions-cell a.btn { flex: 0 0 auto; }
    .action-btn {
        padding: 6px 9px !important;
        border-radius: 9px !important;
        font-size: 12px !important;
        line-height: 1.1;
        min-height: 30px;
    }
    .edit-btn { padding: 6px 10px !important; }
    .table-wrap { overflow-x: auto; }
    table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        background: white;
        min-width: 1240px;
        table-layout: auto;
    }
    th, td {
        padding: 14px 10px;
        border-bottom: 1px solid #e5e7eb;
        text-align: left;
        vertical-align: top;
    }
    th { background: #eff6ff; position: sticky; top: 0; }
    th a {
        color: #0f172a;
        text-decoration: none;
        font-weight: 700;
    }
    th a:hover { text-decoration: underline; }
    tr:hover td { background: #fafcff; }
    .row-Disponible td { background: #f0f7ff; }
    .row-Objetivo td { background: #fff8e1; }
    .row-Elegida td { background: #ecfdf5; }
    .row-Descartada td { background: #fef2f2; }
    .clickable-row { cursor: pointer; }
    .topbar {
        display: flex;
        justify-content: space-between;
        gap: 10px;
        flex-wrap: wrap;
        align-items: center;
    }
    .muted { color: #64748b; font-size: 14px; }
    .pill {
        display: inline-block;
        padding: 4px 9px;
        border-radius: 999px;
        font-size: 11px;
        font-weight: bold;
        background: #e5e7eb;
    }
    .Disponible { background: #dbeafe; }
    .Objetivo { background: #fef3c7; }
    .Elegida { background: #dcfce7; }
    .Descartada { background: #fee2e2; }
    .stats {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 12px;
        margin-bottom: 20px;
    }
    .stat {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 16px;
        box-shadow: 0 6px 18px rgba(15, 23, 42, 0.05);
    }
    .stat-number { font-size: 28px; font-weight: bold; margin-top: 4px; }
    .notes-cell {
        max-width: 220px;
        min-width: 140px;
        white-space: pre-wrap;
        color: #334155;
        font-size: 13px;
    }
    .name-cell { min-width: 150px; font-weight: 600; }
    .team-cell, .pos-cell { min-width: 120px; }
    .filter-bar {
        display: grid;
        grid-template-columns: 2fr 1fr auto;
        gap: 12px;
        align-items: end;
    }
    .result-info { margin-top: 12px; font-size: 14px; color: #475569; }
    .empty-state { text-align: center; color: #64748b; padding: 24px 0; }
    .sticky-filters { position: sticky; top: 12px; z-index: 5; }
    .alert {
        background: #fef2f2;
        color: #991b1b;
        border: 1px solid #fecaca;
        padding: 10px 12px;
        border-radius: 10px;
        margin-bottom: 12px;
    }
    @media (max-width: 900px) {
        .grid, .stats, .grid-2, .filter-bar { grid-template-columns: 1fr; }
        .sticky-filters { position: static; }
    }
</style>
"""

SCRIPT = """
<script>
function normalizeText(value) {
    return (value || "").toLowerCase().trim();
}
function filterRows() {
    const searchEl = document.getElementById("liveSearch");
    const statusEl = document.getElementById("liveStatus");
    if (!searchEl || !statusEl) return;
    const text = normalizeText(searchEl.value);
    const status = normalizeText(statusEl.value);
    const rows = document.querySelectorAll("tbody tr[data-player-row='1']");
    let visible = 0;
    rows.forEach((row) => {
        const haystack = normalizeText(row.dataset.search || "");
        const rowStatus = normalizeText(row.dataset.status || "");
        const matchesText = !text || haystack.includes(text);
        const matchesStatus = !status || rowStatus === status;
        const show = matchesText && matchesStatus;
        row.style.display = show ? "" : "none";
        if (show) visible += 1;
    });
    const countEl = document.getElementById("visibleCount");
    if (countEl) countEl.textContent = visible;
    const empty = document.getElementById("emptyLive");
    if (empty) empty.style.display = visible === 0 ? "" : "none";
}
function clearFilters() {
    const s = document.getElementById("liveSearch");
    const st = document.getElementById("liveStatus");
    if (s) s.value = "";
    if (st) st.value = "";
    filterRows();
}
document.addEventListener("DOMContentLoaded", function () {
    const search = document.getElementById("liveSearch");
    const status = document.getElementById("liveStatus");
    if (search) search.addEventListener("input", filterRows);
    if (status) status.addEventListener("change", filterRows);
    filterRows();
});
</script>
"""


def page(content: str) -> str:
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Draft Web</title>
    {CSS}
</head>
<body>
    <div class="container">{content}</div>
    {SCRIPT}
</body>
</html>"""


def get_current_user(request: Request):
    token = request.cookies.get(SESSION_COOKIE, "")
    if not token:
        return None

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, username, is_admin FROM users")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    for user_id, username, is_admin in rows:
        expected = hash_text(f"{username}:{user_id}")
        if token == expected:
            return {"id": user_id, "username": username, "is_admin": is_admin}
    return None


def require_user(request: Request):
    return get_current_user(request)


def get_stats():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM players")
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM players WHERE status='Disponible'")
    disponible = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM players WHERE status='Objetivo'")
    objetivo = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM players WHERE status='Elegida'")
    elegida = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM players WHERE status='Descartada'")
    descartada = cur.fetchone()[0]
    cur.close()
    conn.close()
    return total, disponible, objetivo, elegida, descartada


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request, error: str = ""):
    user = get_current_user(request)
    if user:
        return RedirectResponse("/", status_code=303)

    msg = '<div class="alert">Usuario o contraseña incorrectos.</div>' if error else ""
    content = f"""
    <div class="login-wrap">
        <div class="card">
            <h1>Entrar</h1>
            <div class="muted">Acceso privado para tu equipo.</div>
            <div style="margin-top:16px;">
                {msg}
                <form action="/login" method="post">
                    <div style="margin-bottom:12px;">
                        <label>Usuario</label>
                        <input name="username" required>
                    </div>
                    <div style="margin-bottom:12px;">
                        <label>Contraseña</label>
                        <input type="password" name="password" required>
                    </div>
                    <button type="submit">Entrar</button>
                </form>
            </div>
        </div>
    </div>
    """
    return page(content)


@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, username, password_hash, is_admin FROM users WHERE username = %s",
        (username.strip(),),
    )
    user = cur.fetchone()
    cur.close()
    conn.close()

    if not user:
        return RedirectResponse("/login?error=1", status_code=303)

    user_id, db_username, password_hash, is_admin = user
    if password_hash != hash_text(password):
        return RedirectResponse("/login?error=1", status_code=303)

    response = RedirectResponse("/", status_code=303)
    response.set_cookie(
        key=SESSION_COOKIE,
        value=hash_text(f"{db_username}:{user_id}"),
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 7,
    )
    return response


@app.get("/logout")
def logout():
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie(SESSION_COOKIE)
    return response


@app.get("/", response_class=HTMLResponse)
def home(request: Request, sort: str = "id", order: str = "desc"):
    user = require_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    allowed = ["id", "name", "team", "position", "status"]
    if sort not in allowed:
        sort = "id"
    order_sql = "ASC" if order == "asc" else "DESC"

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        f"SELECT id, name, team, position, status, COALESCE(notes, '') FROM players ORDER BY {sort} {order_sql}"
    )
    players = cur.fetchall()
    cur.close()
    conn.close()

    total, disponible, objetivo, elegida, descartada = get_stats()

    rows = ""
    for pid, name, team, position, st, notes in players:
        search_blob = " ".join([name or "", team or "", position or "", st or "", notes or ""])
        rows += f"""
        <tr class="row-{html.escape(st)} clickable-row" onclick="window.location='/edit/{pid}'"
            data-player-row="1"
            data-status="{html.escape(st)}"
            data-search="{html.escape(search_blob)}">
            <td class="name-cell">{html.escape(name or "")}</td>
            <td class="team-cell">{html.escape(team or "")}</td>
            <td class="pos-cell">{html.escape(position or "")}</td>
            <td><span class="pill {html.escape(st)}">{html.escape(st)}</span></td>
            <td class="notes-cell">{html.escape(notes or "")}</td>
            <td class="actions-cell">
                <div class="actions-toolbar" onclick="event.stopPropagation();">
                    <a class="btn btn-light action-btn edit-btn" href="/edit/{pid}">Editar</a>
                    <form class="inline-form" action="/status/{pid}" method="post">
                        <input type="hidden" name="status" value="Objetivo">
                        <button class="btn-warning action-btn" type="submit">Objetivo</button>
                    </form>
                    <form class="inline-form" action="/status/{pid}" method="post">
                        <input type="hidden" name="status" value="Elegida">
                        <button class="btn-success action-btn" type="submit">Elegida</button>
                    </form>
                    <form class="inline-form" action="/status/{pid}" method="post">
                        <input type="hidden" name="status" value="Descartada">
                        <button class="btn-danger action-btn" type="submit">Descartada</button>
                    </form>
                    <form class="inline-form" action="/status/{pid}" method="post">
                        <input type="hidden" name="status" value="Disponible">
                        <button class="btn-secondary action-btn" type="submit">Disponible</button>
                    </form>
                    <form class="inline-form" action="/delete/{pid}" method="post" onsubmit="return confirm('¿Borrar esta jugadora?')">
                        <button class="btn-danger action-btn" type="submit">Borrar</button>
                    </form>
                </div>
            </td>
        </tr>
        """

    if not rows:
        rows = '<tr><td colspan="6" class="empty-state">No hay jugadoras todavía.</td></tr>'

    def build_header(field: str, label: str) -> str:
        new_order = "desc" if (sort == field and order == "asc") else "asc"
        arrow = ""
        if sort == field:
            arrow = " ↑" if order == "asc" else " ↓"
        return f'<a href="/?sort={field}&order={new_order}">{label}{arrow}</a>'

    admin_box = ""
    if user["is_admin"]:
        admin_box = """
        <div class="card">
            <h2>Crear usuario</h2>
            <div class="muted">Solo visible para admin.</div>
            <form action="/users/create" method="post" style="margin-top:12px;">
                <div class="grid">
                    <div>
                        <label>Usuario</label>
                        <input name="username" required>
                    </div>
                    <div>
                        <label>Contraseña</label>
                        <input type="password" name="password" required>
                    </div>
                    <div>
                        <label>Rol</label>
                        <select name="is_admin">
                            <option value="0">Usuario</option>
                            <option value="1">Admin</option>
                        </select>
                    </div>
                    <div>
                        <button type="submit">Crear usuario</button>
                    </div>
                </div>
            </form>
        </div>
        """

    content = f"""
    <div class="topbar">
        <div>
            <h1>Draft Web</h1>
            <div class="muted">Usuario: <strong>{html.escape(user["username"])}</strong></div>
        </div>
        <div class="actions-toolbar">
            <a class="btn" href="/export">Exportar Excel</a>
            <a class="btn btn-secondary" href="/logout">Salir</a>
        </div>
    </div>

    <div class="stats">
        <div class="stat"><div class="muted">Total</div><div class="stat-number">{total}</div></div>
        <div class="stat"><div class="muted">Disponibles</div><div class="stat-number">{disponible}</div></div>
        <div class="stat"><div class="muted">Objetivo</div><div class="stat-number">{objetivo}</div></div>
        <div class="stat"><div class="muted">Elegidas / Descartadas</div><div class="stat-number">{elegida} / {descartada}</div></div>
    </div>

    {admin_box}

    <div class="grid-2">
        <div class="card">
            <h2>Añadir jugadora</h2>
            <form action="/add" method="post">
                <div class="grid">
                    <div><label>Nombre</label><input name="name" required></div>
                    <div><label>Equipo</label><input name="team"></div>
                    <div><label>Posición</label><input name="position"></div>
                    <div>
                        <label>Estado</label>
                        <select name="status">
                            <option value="Disponible">Disponible</option>
                            <option value="Objetivo">Objetivo</option>
                            <option value="Elegida">Elegida</option>
                            <option value="Descartada">Descartada</option>
                        </select>
                    </div>
                </div>
                <div style="margin-top:12px;">
                    <label>Notas</label>
                    <textarea name="notes" placeholder="observaciones, pie, prioridad, ronda..."></textarea>
                </div>
                <div style="margin-top:12px;">
                    <button type="submit">Añadir jugadora</button>
                </div>
            </form>
        </div>

        <div class="card">
            <h2>Importar CSV</h2>
            <form action="/import" method="post" enctype="multipart/form-data">
                <label>Archivo CSV</label>
                <input type="file" name="file" accept=".csv" required>
                <div style="margin-top:12px;">
                    <button type="submit">Importar CSV</button>
                </div>
            </form>
            <div class="muted" style="margin-top:10px;">Columnas aceptadas: name, team, position, status, notes</div>
        </div>
    </div>

    <div class="card sticky-filters">
        <h2>Filtros rápidos</h2>
        <div class="filter-bar">
            <div>
                <label>Buscar</label>
                <input id="liveSearch" placeholder="nombre, equipo, posición o notas">
            </div>
            <div>
                <label>Estado</label>
                <select id="liveStatus">
                    <option value="">Todos</option>
                    <option value="Disponible">Disponible</option>
                    <option value="Objetivo">Objetivo</option>
                    <option value="Elegida">Elegida</option>
                    <option value="Descartada">Descartada</option>
                </select>
            </div>
            <div>
                <button type="button" class="btn btn-secondary" onclick="clearFilters()">Limpiar</button>
            </div>
        </div>
        <div class="result-info">Mostrando <strong id="visibleCount">0</strong> jugadoras</div>
    </div>

    <div class="card">
        <h2>Jugadoras</h2>
        <div class="table-wrap">
            <table>
                <thead>
                    <tr>
                        <th>{build_header("name", "Nombre")}</th>
                        <th>{build_header("team", "Equipo")}</th>
                        <th>{build_header("position", "Posición")}</th>
                        <th>{build_header("status", "Estado")}</th>
                        <th>Notas</th>
                        <th>Acciones</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                    <tr id="emptyLive" style="display:none;">
                        <td colspan="6" class="empty-state">No hay resultados con esos filtros.</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
    """
    return page(content)


@app.post("/users/create")
def create_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    is_admin: str = Form("0")
):
    user = require_user(request)
    if not user or not user["is_admin"]:
        return RedirectResponse("/login", status_code=303)

    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (username, password_hash, is_admin) VALUES (%s, %s, %s)",
            (username.strip(), hash_text(password), is_admin == "1"),
        )
        conn.commit()
    except Exception:
        conn.rollback()
    finally:
        cur.close()
        conn.close()

    return RedirectResponse("/", status_code=303)


@app.get("/edit/{player_id}", response_class=HTMLResponse)
def edit_page(player_id: int, request: Request):
    user = require_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, name, team, position, status, COALESCE(notes, '') FROM players WHERE id = %s",
        (player_id,),
    )
    player = cur.fetchone()
    cur.close()
    conn.close()

    if not player:
        return page('<div class="card"><h2>No encontrada</h2><a class="btn" href="/">Volver</a></div>')

    pid, name, team, position, status, notes = player

    content = f"""
    <div class="card">
        <h1>Editar jugadora</h1>
        <form action="/update/{pid}" method="post">
            <div class="grid">
                <div><label>Nombre</label><input name="name" value="{html.escape(name or '')}" required></div>
                <div><label>Equipo</label><input name="team" value="{html.escape(team or '')}"></div>
                <div><label>Posición</label><input name="position" value="{html.escape(position or '')}"></div>
                <div>
                    <label>Estado</label>
                    <select name="status">
                        <option value="Disponible" {"selected" if status == "Disponible" else ""}>Disponible</option>
                        <option value="Objetivo" {"selected" if status == "Objetivo" else ""}>Objetivo</option>
                        <option value="Elegida" {"selected" if status == "Elegida" else ""}>Elegida</option>
                        <option value="Descartada" {"selected" if status == "Descartada" else ""}>Descartada</option>
                    </select>
                </div>
            </div>
            <div style="margin-top:12px;">
                <label>Notas</label>
                <textarea name="notes">{html.escape(notes or '')}</textarea>
            </div>
            <div class="actions-toolbar" style="margin-top:16px;">
                <button type="submit">Guardar cambios</button>
                <a class="btn btn-secondary" href="/">Cancelar</a>
            </div>
        </form>
    </div>
    """
    return page(content)


@app.post("/add")
def add(
    request: Request,
    name: str = Form(...),
    team: str = Form(""),
    position: str = Form(""),
    status: str = Form("Disponible"),
    notes: str = Form("")
):
    user = require_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO players (name, team, position, status, notes) VALUES (%s, %s, %s, %s, %s)",
        (name.strip(), team.strip(), position.strip(), status, notes.strip()),
    )
    conn.commit()
    cur.close()
    conn.close()
    return RedirectResponse("/", status_code=303)


@app.post("/update/{player_id}")
def update_player(
    player_id: int,
    request: Request,
    name: str = Form(...),
    team: str = Form(""),
    position: str = Form(""),
    status: str = Form("Disponible"),
    notes: str = Form("")
):
    user = require_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE players SET name=%s, team=%s, position=%s, status=%s, notes=%s WHERE id=%s",
        (name.strip(), team.strip(), position.strip(), status, notes.strip(), player_id),
    )
    conn.commit()
    cur.close()
    conn.close()
    return RedirectResponse("/", status_code=303)


@app.post("/status/{player_id}")
def change_status(player_id: int, request: Request, status: str = Form(...)):
    user = require_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE players SET status = %s WHERE id = %s", (status, player_id))
    conn.commit()
    cur.close()
    conn.close()
    return RedirectResponse("/", status_code=303)


@app.post("/delete/{player_id}")
def delete_player(player_id: int, request: Request):
    user = require_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM players WHERE id = %s", (player_id,))
    conn.commit()
    cur.close()
    conn.close()
    return RedirectResponse("/", status_code=303)


@app.post("/import")
def import_csv(request: Request, file: UploadFile = File(...)):
    user = require_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    content = file.file.read().decode("utf-8-sig").splitlines()
    reader = csv.DictReader(content)

    conn = get_conn()
    cur = conn.cursor()

    for row in reader:
        name = (row.get("name") or row.get("nombre") or "").strip()
        team = (row.get("team") or row.get("equipo") or "").strip()
        position = (row.get("position") or row.get("posicion") or row.get("posición") or "").strip()
        status = (row.get("status") or row.get("estado") or "Disponible").strip() or "Disponible"
        notes = (row.get("notes") or row.get("notas") or "").strip()
        if name:
            cur.execute(
                "INSERT INTO players (name, team, position, status, notes) VALUES (%s, %s, %s, %s, %s)",
                (name, team, position, status, notes),
            )

    conn.commit()
    cur.close()
    conn.close()
    return RedirectResponse("/", status_code=303)


@app.get("/export")
def export_excel(request: Request):
    user = require_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT name, team, position, status, COALESCE(notes, '') FROM players ORDER BY id DESC")
    players = cur.fetchall()
    cur.close()
    conn.close()

    wb = Workbook()
    ws = wb.active
    ws.title = "Jugadoras"
    ws.append(["Nombre", "Equipo", "Posición", "Estado", "Notas"])
    for row in players:
        ws.append(row)

    stream = io.BytesIO()
    wb.save(stream)
    stream.seek(0)

    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=jugadoras.xlsx"},
    )
