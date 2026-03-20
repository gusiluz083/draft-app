
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
ADMIN_USER = os.getenv("ADMIN_USER", "admin").strip()
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

if not DATABASE_URL:
    raise RuntimeError("Falta la variable de entorno DATABASE_URL")

SESSION_COOKIE = "draft_session"
TEAM_COOKIE = "draft_team"
TEAMS = ["PILARES", "MADAM", "COLS"]
STATUSES = ["Disponible", "Objetivo", "Elegida", "Descartada", "Fichada por otro equipo"]

def hash_text(value: str) -> str:
    return hashlib.sha256((value + SECRET_KEY).encode("utf-8")).hexdigest()

def get_conn():
    return psycopg2.connect(DATABASE_URL)

def ensure_admin():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE username = %s", (ADMIN_USER,))
    row = cur.fetchone()
    if row:
        cur.execute("UPDATE users SET password_hash = %s, is_admin = TRUE WHERE username = %s",
                    (hash_text(ADMIN_PASSWORD), ADMIN_USER))
    else:
        cur.execute("INSERT INTO users (username, password_hash, is_admin) VALUES (%s, %s, %s)",
                    (ADMIN_USER, hash_text(ADMIN_PASSWORD), True))
    conn.commit()
    cur.close()
    conn.close()

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
    cur.execute("ALTER TABLE players ADD COLUMN IF NOT EXISTS board_team TEXT DEFAULT 'PILARES'")
    cur.execute("ALTER TABLE players ADD COLUMN IF NOT EXISTS draft_round INTEGER")
    conn.commit()
    cur.close()
    conn.close()
    ensure_admin()

init_db()

CSS = """
<style>
* { box-sizing: border-box; }
body { font-family: Arial, sans-serif; background: linear-gradient(180deg,#eef3f9 0%,#f8fafc 100%); margin:0; padding:20px; color:#1f2937; }
.container { max-width:1380px; margin:0 auto; }
.card { background:white; border-radius:18px; padding:22px; box-shadow:0 10px 30px rgba(15,23,42,0.08); margin-bottom:18px; border:1px solid #e5e7eb; }
.login-wrap { max-width:420px; margin:80px auto; }
h1,h2 { margin-top:0; }
label { display:block; font-size:14px; margin-bottom:6px; font-weight:bold; }
input,select,textarea,button { width:100%; padding:11px 12px; border:1px solid #cbd5e1; border-radius:10px; font-size:14px; }
textarea { min-height:90px; resize:vertical; }
button,.btn,a.btn { background:#2563eb; color:white; border:none; cursor:pointer; text-decoration:none; display:inline-flex; align-items:center; justify-content:center; width:auto; white-space:nowrap; font-weight:600; }
.btn-secondary { background:#475569; } .btn-success { background:#16a34a; } .btn-danger { background:#dc2626; } .btn-warning { background:#d97706; } .btn-light { background:#0f766e; } .btn-dark { background:#0f172a; }
.inline-form { display:inline; margin:0; }
.actions-toolbar { display:flex; gap:6px; flex-wrap:wrap; align-items:center; }
.action-btn { padding:6px 9px !important; border-radius:9px !important; font-size:12px !important; line-height:1.1; min-height:30px; }
.grid { display:grid; grid-template-columns:repeat(4,1fr); gap:12px; align-items:end; }
.grid-2 { display:grid; grid-template-columns:2fr 1fr; gap:20px; }
.grid-3 { display:grid; grid-template-columns:repeat(3,1fr); gap:14px; }
.team-cards { display:grid; grid-template-columns:repeat(3,1fr); gap:14px; }
.team-card { border:1px solid #dbe3ef; border-radius:16px; padding:18px; background:#f8fbff; text-align:center; }
.tabs { display:flex; gap:10px; flex-wrap:wrap; margin-bottom:18px; }
.tab { padding:10px 14px; border-radius:999px; background:#e2e8f0; color:#0f172a; text-decoration:none; font-weight:700; }
.tab.active { background:#2563eb; color:white; }
.topbar { display:flex; justify-content:space-between; gap:10px; flex-wrap:wrap; align-items:center; }
.table-wrap { overflow-x:auto; }
table { width:100%; border-collapse:separate; border-spacing:0; background:white; min-width:1160px; }
th,td { padding:12px 10px; border-bottom:1px solid #e5e7eb; text-align:left; vertical-align:top; }
th { background:#eff6ff; }
th a { color:#0f172a; text-decoration:none; font-weight:700; }
.muted { color:#64748b; font-size:14px; }
.alert { background:#fef2f2; color:#991b1b; border:1px solid #fecaca; padding:10px 12px; border-radius:10px; margin-bottom:12px; }
.pill { display:inline-block; padding:4px 9px; border-radius:999px; font-size:11px; font-weight:bold; background:#e5e7eb; }
.Disponible { background:#dbeafe; } .Objetivo { background:#fef3c7; } .Elegida { background:#dcfce7; } .Descartada { background:#fee2e2; } .Fichada_por_otro_equipo { background:#e5e7eb; }
.stats { display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin-bottom:20px; }
.stat { background:white; border:1px solid #e2e8f0; border-radius:16px; padding:16px; }
.stat-number { font-size:28px; font-weight:bold; margin-top:4px; }
@media (max-width:900px) { .grid,.grid-2,.grid-3,.team-cards,.stats { grid-template-columns:1fr; } }
</style>
"""

SCRIPT = """
<script>
function normalizeText(v){return (v||'').toLowerCase().trim();}
function filterRows(){
 const s=document.getElementById('liveSearch'); const st=document.getElementById('liveStatus');
 if(!s||!st) return;
 const text=normalizeText(s.value), status=normalizeText(st.value);
 const rows=document.querySelectorAll("tbody tr[data-player-row='1']");
 let visible=0;
 rows.forEach((row)=>{const hay=normalizeText(row.dataset.search||''); const rs=normalizeText(row.dataset.status||''); const show=(!text||hay.includes(text))&&(!status||rs===status); row.style.display=show?'':'none'; if(show) visible+=1;});
 const c=document.getElementById('visibleCount'); if(c) c.textContent=visible;
}
function clearFilters(){document.getElementById('liveSearch').value=''; document.getElementById('liveStatus').value=''; filterRows();}
document.addEventListener('DOMContentLoaded',()=>{const s=document.getElementById('liveSearch'); const st=document.getElementById('liveStatus'); if(s)s.addEventListener('input',filterRows); if(st)st.addEventListener('change',filterRows); filterRows();});
</script>
"""

def page(content: str) -> str:
    return f"<!DOCTYPE html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'><title>Draft Web</title>{CSS}</head><body><div class='container'>{content}</div>{SCRIPT}</body></html>"

def get_current_user(request: Request):
    token=request.cookies.get(SESSION_COOKIE,'')
    if not token: return None
    conn=get_conn(); cur=conn.cursor(); cur.execute('SELECT id, username, is_admin FROM users'); rows=cur.fetchall(); cur.close(); conn.close()
    for user_id, username, is_admin in rows:
        if token == hash_text(f"{username}:{user_id}"):
            return {'id': user_id, 'username': username, 'is_admin': is_admin}
    return None

def require_user(request: Request):
    return get_current_user(request)

def get_team(request: Request):
    team=request.cookies.get(TEAM_COOKIE,'')
    return team if team in TEAMS else None

def get_stats(board_team: str):
    conn=get_conn(); cur=conn.cursor()
    cur.execute('SELECT COUNT(*) FROM players WHERE board_team=%s',(board_team,)); total=cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM players WHERE board_team=%s AND status='Objetivo'",(board_team,)); objetivos=cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM players WHERE board_team=%s AND status='Elegida'",(board_team,)); elegidas=cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM players WHERE board_team=%s AND status='Fichada por otro equipo'",(board_team,)); otros=cur.fetchone()[0]
    cur.close(); conn.close()
    return total, objetivos, elegidas, otros

def status_class(status: str) -> str:
    return (status or '').replace(' ','_')

@app.get('/login', response_class=HTMLResponse)
def login_page(request: Request, error: str = ''):
    if get_current_user(request): return RedirectResponse('/select-team', status_code=303)
    msg = '<div class="alert">Usuario o contraseña incorrectos.</div>' if error else ''
    return page(f"<div class='login-wrap'><div class='card'><h1>Entrar</h1><div class='muted'>Acceso privado para tu equipo.</div>{msg}<form action='/login' method='post'><div style='margin:12px 0;'><label>Usuario</label><input name='username' required></div><div style='margin:12px 0;'><label>Contraseña</label><input type='password' name='password' required></div><button type='submit'>Entrar</button></form></div></div>")

@app.post('/login')
def login(username: str = Form(...), password: str = Form(...)):
    username=username.strip(); ensure_admin()
    if username == ADMIN_USER and password == ADMIN_PASSWORD:
        conn=get_conn(); cur=conn.cursor(); cur.execute('SELECT id, username FROM users WHERE username=%s',(ADMIN_USER,)); row=cur.fetchone(); cur.close(); conn.close()
        if row:
            user_id, db_username = row
            r=RedirectResponse('/select-team', status_code=303); r.set_cookie(SESSION_COOKIE, hash_text(f"{db_username}:{user_id}"), httponly=True, samesite='lax', max_age=604800); return r
    conn=get_conn(); cur=conn.cursor(); cur.execute('SELECT id, username, password_hash FROM users WHERE username=%s',(username,)); row=cur.fetchone(); cur.close(); conn.close()
    if not row: return RedirectResponse('/login?error=1', status_code=303)
    user_id, db_username, password_hash=row
    if password_hash != hash_text(password): return RedirectResponse('/login?error=1', status_code=303)
    r=RedirectResponse('/select-team', status_code=303); r.set_cookie(SESSION_COOKIE, hash_text(f"{db_username}:{user_id}"), httponly=True, samesite='lax', max_age=604800); return r

@app.get('/logout')
def logout():
    r=RedirectResponse('/login', status_code=303); r.delete_cookie(SESSION_COOKIE); r.delete_cookie(TEAM_COOKIE); return r

@app.get('/select-team', response_class=HTMLResponse)
def select_team_page(request: Request):
    user=require_user(request)
    if not user: return RedirectResponse('/login', status_code=303)
    cards=''.join([f"<div class='team-card'><h2>{team}</h2><div class='muted' style='margin-bottom:12px;'>Entrar al tablero de {team}</div><form action='/select-team' method='post'><input type='hidden' name='team' value='{team}'><button type='submit'>Entrar en {team}</button></form></div>" for team in TEAMS])
    return page(f"<div class='card'><div class='topbar'><div><h1>Elegir equipo</h1><div class='muted'>Usuario: <strong>{html.escape(user['username'])}</strong></div></div><a class='btn btn-secondary' href='/logout'>Salir</a></div><div class='team-cards' style='margin-top:18px;'>{cards}</div></div>")

@app.post('/select-team')
def select_team(request: Request, team: str = Form(...)):
    if not require_user(request): return RedirectResponse('/login', status_code=303)
    if team not in TEAMS: return RedirectResponse('/select-team', status_code=303)
    r=RedirectResponse('/', status_code=303); r.set_cookie(TEAM_COOKIE, team, httponly=True, samesite='lax', max_age=604800); return r

@app.get('/', response_class=HTMLResponse)
def home(request: Request, tab: str='database', sort: str='id', order: str='desc'):
    user=require_user(request)
    if not user: return RedirectResponse('/login', status_code=303)
    board_team=get_team(request)
    if not board_team: return RedirectResponse('/select-team', status_code=303)
    if tab not in ['database','objectives','final']: tab='database'
    if sort not in ['id','name','team','position','status','draft_round']: sort='id'
    order_sql='ASC' if order=='asc' else 'DESC'
    sql='SELECT id, name, team, position, status, COALESCE(notes,\'\'), draft_round FROM players WHERE board_team=%s'
    params=[board_team]
    if tab=='objectives': sql += " AND status='Objetivo'"
    elif tab=='final': sql += " AND status='Elegida'"
    sql += f' ORDER BY {sort} {order_sql}'
    conn=get_conn(); cur=conn.cursor(); cur.execute(sql, params); players=cur.fetchall(); cur.close(); conn.close()
    total, objetivos, elegidas, otros = get_stats(board_team)

    def head(field,label):
        new_order='desc' if (sort==field and order=='asc') else 'asc'
        arrow=' ↑' if (sort==field and order=='asc') else (' ↓' if sort==field else '')
        return f"<a href='/?tab={tab}&sort={field}&order={new_order}'>{label}{arrow}</a>"

    rows=''
    for pid, name, team, position, status, notes, draft_round in players:
        search_blob=' '.join([name or '', team or '', position or '', status or '', notes or ''])
        round_display=draft_round if draft_round else ''
        actions=[f"<a class='btn btn-light action-btn' href='/edit/{pid}'>Editar</a>"]
        if tab=='database':
            actions += [
                f"<form class='inline-form' action='/status/{pid}' method='post'><input type='hidden' name='status' value='Objetivo'><button class='btn-warning action-btn' type='submit'>Objetivo</button></form>",
                f"<form class='inline-form' action='/status/{pid}' method='post'><input type='hidden' name='status' value='Elegida'><button class='btn-success action-btn' type='submit'>Elegida</button></form>",
                f"<form class='inline-form' action='/status/{pid}' method='post'><input type='hidden' name='status' value='Descartada'><button class='btn-danger action-btn' type='submit'>Descartada</button></form>",
            ]
        elif tab=='objectives':
            opts="<option value=''>Ronda</option>" + ''.join([f"<option value='{i}' {'selected' if draft_round==i else ''}>{i}</option>" for i in range(1,11)])
            actions += [
                f"<form class='inline-form' action='/round/{pid}' method='post'><select name='draft_round' style='width:90px;padding:6px 8px;'>{opts}</select><button class='btn-dark action-btn' type='submit'>Guardar</button></form>",
                f"<form class='inline-form' action='/status/{pid}' method='post'><input type='hidden' name='status' value='Elegida'><button class='btn-success action-btn' type='submit'>Elegida</button></form>",
                f"<form class='inline-form' action='/status/{pid}' method='post'><input type='hidden' name='status' value='Descartada'><button class='btn-danger action-btn' type='submit'>Descartada</button></form>",
                f"<form class='inline-form' action='/status/{pid}' method='post'><input type='hidden' name='status' value='Fichada por otro equipo'><button class='btn-secondary action-btn' type='submit'>Otro equipo</button></form>",
            ]
        else:
            actions += [
                f"<form class='inline-form' action='/status/{pid}' method='post'><input type='hidden' name='status' value='Descartada'><button class='btn-danger action-btn' type='submit'>Descartada</button></form>",
                f"<form class='inline-form' action='/status/{pid}' method='post'><input type='hidden' name='status' value='Fichada por otro equipo'><button class='btn-secondary action-btn' type='submit'>Otro equipo</button></form>",
            ]
        actions_html="<div class='actions-toolbar'>"+''.join(actions)+"</div>"
        rows += f"<tr data-player-row='1' data-status='{html.escape(status)}' data-search='{html.escape(search_blob)}'><td>{html.escape(name or '')}</td><td>{html.escape(team or '')}</td><td>{html.escape(position or '')}</td><td><span class='pill {status_class(status)}'>{html.escape(status)}</span></td><td>{html.escape(str(round_display))}</td><td>{html.escape(notes or '')}</td><td>{actions_html}</td></tr>"
    if not rows: rows = "<tr><td colspan='7' class='muted'>No hay jugadoras en esta pestaña.</td></tr>"

    admin_box=''
    if user['is_admin']:
        admin_box="<div class='card'><h2>Crear usuario</h2><form action='/users/create' method='post'><div class='grid'><div><label>Usuario</label><input name='username' required></div><div><label>Contraseña</label><input type='password' name='password' required></div><div><label>Rol</label><select name='is_admin'><option value='0'>Usuario</option><option value='1'>Admin</option></select></div><div><button type='submit'>Crear usuario</button></div></div></form></div>"

    add_box=''
    if tab=='database':
        add_box=f"<div class='grid-2'><div class='card'><h2>Base de datos</h2><form action='/add' method='post'><div class='grid'><div><label>Nombre</label><input name='name' required></div><div><label>Equipo actual</label><input name='team'></div><div><label>Posición</label><input name='position'></div><div><label>Estado</label><select name='status'><option value='Disponible'>Disponible</option><option value='Objetivo'>Objetivo</option><option value='Elegida'>Elegida</option><option value='Descartada'>Descartada</option><option value='Fichada por otro equipo'>Fichada por otro equipo</option></select></div></div><div style='margin-top:12px;'><label>Notas</label><textarea name='notes'></textarea></div><div style='margin-top:12px;'><button type='submit'>Añadir jugadora</button></div></form></div><div class='card'><h2>Importar CSV</h2><form action='/import' method='post' enctype='multipart/form-data'><label>Archivo CSV</label><input type='file' name='file' accept='.csv' required><div style='margin-top:12px;'><button type='submit'>Importar CSV</button></div></form><div class='muted' style='margin-top:10px;'>Se importará dentro del equipo {board_team}.</div></div></div>"

    content=f"<div class='topbar'><div><h1>{board_team}</h1><div class='muted'>Usuario: <strong>{html.escape(user['username'])}</strong></div></div><div class='actions-toolbar'><a class='btn btn-secondary' href='/select-team'>Cambiar equipo</a><a class='btn' href='/export?tab={tab}'>Exportar Excel</a><a class='btn btn-secondary' href='/logout'>Salir</a></div></div><div class='stats'><div class='stat'><div class='muted'>Total jugadoras</div><div class='stat-number'>{total}</div></div><div class='stat'><div class='muted'>Objetivos</div><div class='stat-number'>{objetivos}</div></div><div class='stat'><div class='muted'>Plantilla definitiva</div><div class='stat-number'>{elegidas}</div></div><div class='stat'><div class='muted'>Fichadas por otro equipo</div><div class='stat-number'>{otros}</div></div></div>{admin_box}<div class='tabs'><a class='tab {'active' if tab=='database' else ''}' href='/?tab=database'>Base de datos</a><a class='tab {'active' if tab=='objectives' else ''}' href='/?tab=objectives'>Objetivos</a><a class='tab {'active' if tab=='final' else ''}' href='/?tab=final'>Plantilla definitiva</a></div>{add_box}<div class='card'><h2>Filtros</h2><div class='grid-3'><div><label>Buscar</label><input id='liveSearch' placeholder='nombre, equipo, posición, notas'></div><div><label>Estado</label><select id='liveStatus'><option value=''>Todos</option><option value='Disponible'>Disponible</option><option value='Objetivo'>Objetivo</option><option value='Elegida'>Elegida</option><option value='Descartada'>Descartada</option><option value='Fichada por otro equipo'>Fichada por otro equipo</option></select></div><div style='display:flex;align-items:end;'><button type='button' class='btn btn-secondary' onclick='clearFilters()'>Limpiar</button></div></div><div class='muted' style='margin-top:10px;'>Mostrando <strong id='visibleCount'>0</strong> jugadoras</div></div><div class='card'><h2>{'Base de datos' if tab=='database' else 'Objetivos' if tab=='objectives' else 'Plantilla definitiva'}</h2><div class='table-wrap'><table><thead><tr><th>{head('name','Nombre')}</th><th>{head('team','Equipo actual')}</th><th>{head('position','Posición')}</th><th>{head('status','Estado')}</th><th>{head('draft_round','Ronda')}</th><th>Notas</th><th>Acciones</th></tr></thead><tbody>{rows}</tbody></table></div></div>"
    return page(content)

@app.post('/users/create')
def create_user(request: Request, username: str = Form(...), password: str = Form(...), is_admin: str = Form('0')):
    user=require_user(request)
    if not user or not user['is_admin']: return RedirectResponse('/login', status_code=303)
    conn=get_conn(); cur=conn.cursor()
    try:
        cur.execute('INSERT INTO users (username, password_hash, is_admin) VALUES (%s,%s,%s)', (username.strip(), hash_text(password), is_admin=='1')); conn.commit()
    except Exception:
        conn.rollback()
    finally:
        cur.close(); conn.close()
    return RedirectResponse('/', status_code=303)

@app.post('/add')
def add(request: Request, name: str = Form(...), team: str = Form(''), position: str = Form(''), status: str = Form('Disponible'), notes: str = Form('')):
    user=require_user(request); board_team=get_team(request)
    if not user: return RedirectResponse('/login', status_code=303)
    if not board_team: return RedirectResponse('/select-team', status_code=303)
    conn=get_conn(); cur=conn.cursor()
    cur.execute('INSERT INTO players (name, team, position, status, notes, board_team) VALUES (%s,%s,%s,%s,%s,%s)', (name.strip(), team.strip(), position.strip(), status, notes.strip(), board_team))
    conn.commit(); cur.close(); conn.close()
    return RedirectResponse('/?tab=database', status_code=303)

@app.get('/edit/{player_id}', response_class=HTMLResponse)
def edit_page(player_id: int, request: Request):
    user=require_user(request); board_team=get_team(request)
    if not user: return RedirectResponse('/login', status_code=303)
    if not board_team: return RedirectResponse('/select-team', status_code=303)
    conn=get_conn(); cur=conn.cursor(); cur.execute('SELECT id,name,team,position,status,COALESCE(notes,\'\'),COALESCE(draft_round,0),board_team FROM players WHERE id=%s',(player_id,)); row=cur.fetchone(); cur.close(); conn.close()
    if not row or row[7] != board_team: return page("<div class='card'><h2>No encontrada</h2><a class='btn' href='/'>Volver</a></div>")
    pid,name,team,position,status,notes,draft_round,_ = row
    status_options=''.join([f"<option value='{s}' {'selected' if s==status else ''}>{s}</option>" for s in STATUSES])
    round_options="<option value=''>Sin ronda</option>" + ''.join([f"<option value='{i}' {'selected' if draft_round==i else ''}>{i}</option>" for i in range(1,11)])
    return page(f"<div class='card'><h1>Editar jugadora</h1><form action='/update/{pid}' method='post'><div class='grid'><div><label>Nombre</label><input name='name' value='{html.escape(name or '')}' required></div><div><label>Equipo actual</label><input name='team' value='{html.escape(team or '')}'></div><div><label>Posición</label><input name='position' value='{html.escape(position or '')}'></div><div><label>Estado</label><select name='status'>{status_options}</select></div></div><div class='grid' style='margin-top:12px;'><div><label>Ronda draft</label><select name='draft_round'>{round_options}</select></div></div><div style='margin-top:12px;'><label>Notas</label><textarea name='notes'>{html.escape(notes or '')}</textarea></div><div class='actions-toolbar' style='margin-top:16px;'><button type='submit'>Guardar cambios</button><a class='btn btn-secondary' href='/'>Cancelar</a></div></form></div>")

@app.post('/update/{player_id}')
def update_player(player_id: int, request: Request, name: str = Form(...), team: str = Form(''), position: str = Form(''), status: str = Form('Disponible'), notes: str = Form(''), draft_round: str = Form('')):
    user=require_user(request); board_team=get_team(request)
    if not user: return RedirectResponse('/login', status_code=303)
    if not board_team: return RedirectResponse('/select-team', status_code=303)
    round_value = int(draft_round) if str(draft_round).isdigit() else None
    conn=get_conn(); cur=conn.cursor(); cur.execute('UPDATE players SET name=%s, team=%s, position=%s, status=%s, notes=%s, draft_round=%s WHERE id=%s AND board_team=%s', (name.strip(), team.strip(), position.strip(), status, notes.strip(), round_value, player_id, board_team)); conn.commit(); cur.close(); conn.close()
    return RedirectResponse('/', status_code=303)

@app.post('/status/{player_id}')
def change_status(player_id: int, request: Request, status: str = Form(...)):
    user=require_user(request); board_team=get_team(request)
    if not user: return RedirectResponse('/login', status_code=303)
    if not board_team: return RedirectResponse('/select-team', status_code=303)
    conn=get_conn(); cur=conn.cursor(); cur.execute('UPDATE players SET status=%s WHERE id=%s AND board_team=%s', (status, player_id, board_team)); conn.commit(); cur.close(); conn.close()
    if status=='Elegida': return RedirectResponse('/?tab=final', status_code=303)
    if status=='Objetivo': return RedirectResponse('/?tab=objectives', status_code=303)
    return RedirectResponse('/', status_code=303)

@app.post('/round/{player_id}')
def save_round(player_id: int, request: Request, draft_round: str = Form('')):
    user=require_user(request); board_team=get_team(request)
    if not user: return RedirectResponse('/login', status_code=303)
    if not board_team: return RedirectResponse('/select-team', status_code=303)
    round_value = int(draft_round) if str(draft_round).isdigit() else None
    conn=get_conn(); cur=conn.cursor(); cur.execute('UPDATE players SET draft_round=%s WHERE id=%s AND board_team=%s', (round_value, player_id, board_team)); conn.commit(); cur.close(); conn.close()
    return RedirectResponse('/?tab=objectives', status_code=303)

@app.post('/import')
def import_csv(request: Request, file: UploadFile = File(...)):
    user=require_user(request); board_team=get_team(request)
    if not user: return RedirectResponse('/login', status_code=303)
    if not board_team: return RedirectResponse('/select-team', status_code=303)
    reader=csv.DictReader(file.file.read().decode('utf-8-sig').splitlines())
    conn=get_conn(); cur=conn.cursor()
    for row in reader:
        name=(row.get('name') or row.get('nombre') or '').strip()
        team=(row.get('team') or row.get('equipo') or '').strip()
        position=(row.get('position') or row.get('posicion') or row.get('posición') or '').strip()
        status=(row.get('status') or row.get('estado') or 'Disponible').strip() or 'Disponible'
        notes=(row.get('notes') or row.get('notas') or '').strip()
        rnd=(row.get('draft_round') or row.get('ronda') or '').strip()
        round_value=int(rnd) if rnd.isdigit() else None
        if name:
            cur.execute('INSERT INTO players (name, team, position, status, notes, board_team, draft_round) VALUES (%s,%s,%s,%s,%s,%s,%s)', (name, team, position, status, notes, board_team, round_value))
    conn.commit(); cur.close(); conn.close()
    return RedirectResponse('/?tab=database', status_code=303)

@app.get('/export')
def export_excel(request: Request, tab: str = 'database'):
    user=require_user(request); board_team=get_team(request)
    if not user: return RedirectResponse('/login', status_code=303)
    if not board_team: return RedirectResponse('/select-team', status_code=303)
    sql='SELECT name, team, position, status, COALESCE(draft_round, NULL), COALESCE(notes,\'\') FROM players WHERE board_team=%s'
    params=[board_team]
    if tab=='objectives': sql += " AND status='Objetivo'"
    elif tab=='final': sql += " AND status='Elegida'"
    sql += ' ORDER BY id DESC'
    conn=get_conn(); cur=conn.cursor(); cur.execute(sql, params); rows=cur.fetchall(); cur.close(); conn.close()
    wb=Workbook(); ws=wb.active; ws.title=board_team; ws.append(['Nombre','Equipo actual','Posición','Estado','Ronda','Notas'])
    for row in rows: ws.append(row)
    stream=io.BytesIO(); wb.save(stream); stream.seek(0)
    return StreamingResponse(stream, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', headers={'Content-Disposition': f'attachment; filename={board_team.lower()}_{tab}.xlsx'})
