from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="Draft Manager - Rivales Scouting")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Player(BaseModel):
    dorsal: Optional[str] = ""
    name: str
    position: Optional[str] = ""

class Match(BaseModel):
    opponent: str
    date: Optional[str] = ""
    competition: Optional[str] = ""
    result: Optional[str] = ""

class Rival(BaseModel):
    id: int
    name: str
    players: List[Player] = []
    matches: List[Match] = []
    notes: Optional[str] = ""

rivals: List[Rival] = [
    Rival(id=1, name="Vellakas FC"),
]
next_id = 2

@app.get("/", response_class=HTMLResponse)
def home():
    return page()

@app.get("/rivals", response_class=HTMLResponse)
def rivals_page():
    return page()

@app.get("/rivales", response_class=HTMLResponse)
def rivales_page():
    return page()

@app.get("/api/rivals")
def get_rivals():
    return rivals

@app.post("/api/rivals")
def create_rival(payload: dict):
    global next_id
    name = (payload.get("name") or "").strip()
    if not name:
        return {"error": "Nombre obligatorio"}
    rival = Rival(id=next_id, name=name)
    rivals.append(rival)
    next_id += 1
    return rival

@app.delete("/api/rivals/{rival_id}")
def delete_rival(rival_id: int):
    global rivals
    rivals = [r for r in rivals if r.id != rival_id]
    return {"ok": True}

@app.post("/api/rivals/{rival_id}/players")
def add_player(rival_id: int, player: Player):
    for r in rivals:
        if r.id == rival_id:
            r.players.append(player)
            return r
    return {"error": "Rival no encontrado"}

@app.post("/api/rivals/{rival_id}/matches")
def add_match(rival_id: int, match: Match):
    for r in rivals:
        if r.id == rival_id:
            r.matches.append(match)
            return r
    return {"error": "Rival no encontrado"}

@app.post("/api/rivals/{rival_id}/notes")
def save_notes(rival_id: int, payload: dict):
    for r in rivals:
        if r.id == rival_id:
            r.notes = payload.get("notes", "")
            return r
    return {"error": "Rival no encontrado"}

def page():
    return """
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Rivales - Scouting</title>
<style>
*{box-sizing:border-box}body{margin:0;font-family:Arial,Helvetica,sans-serif;background:#f3f7fc;color:#06122e}.top{margin:26px;background:linear-gradient(90deg,#35b6e8,#071027);border-radius:22px;padding:20px 22px;color:white;box-shadow:0 18px 36px #0002}.top h1{margin:0;font-size:34px}.top p{margin:4px 0 0;font-size:13px}.wrap{display:grid;grid-template-columns:224px 1fr;gap:14px;margin:0 26px}.side,.card{background:white;border:1px solid #dbe6f5;border-radius:18px;box-shadow:0 10px 24px #0013}.side{padding:12px;height:max-content}.side-head{display:flex;justify-content:space-between;align-items:center;font-weight:800;margin:4px 2px 14px}.badge{background:#d9fff0;color:#008060;border-radius:999px;font-size:11px;padding:6px 10px;font-weight:800}.rival-btn{display:block;width:100%;text-align:left;border:1px solid #d6e1f2;background:#f8fafc;color:#06122e;border-radius:12px;padding:12px 10px;margin-bottom:8px;cursor:pointer;opacity:1}.rival-btn strong{display:block;font-size:13px;color:inherit}.rival-btn span{display:block;font-size:11px;color:inherit;opacity:.8}.rival-btn.active{background:#06122e;color:white;border-color:#06122e}.add-row{display:flex;gap:8px;margin-top:10px}input,textarea{border:1px solid #cbd9ec;border-radius:10px;padding:10px;background:white;color:#06122e}input{height:34px}.side input{width:100%}button{border:0;border-radius:10px;background:#06122e;color:white;font-weight:800;padding:9px 14px;cursor:pointer}.main h2{margin:38px 0 4px}.crumb{display:inline-block;background:#e9f2ff;border-radius:999px;padding:7px 12px;font-weight:800;font-size:12px}.card{margin-top:8px;overflow:hidden}.card-title{display:flex;justify-content:space-between;padding:14px;border-bottom:1px solid #e1e8f3;font-weight:900}.card-body{padding:12px}.form-line{display:grid;grid-template-columns:72px 1fr 120px auto;gap:8px}.match-line{display:grid;grid-template-columns:1fr 120px 230px 96px auto;gap:8px}textarea{width:100%;min-height:70px}.muted{font-size:12px;color:#50627d}.delete{float:right;background:#ffd9d9;color:#b00000}.empty{padding:4px 0 10px}.player-list,.match-list{font-size:13px;line-height:1.9}.player-list div,.match-list div{border-bottom:1px solid #edf2f8;padding:4px 0}@media(max-width:800px){.wrap{grid-template-columns:1fr}.form-line,.match-line{grid-template-columns:1fr}.top h1{font-size:28px}}
</style>
</head>
<body>
<header class="top"><h1>Rivales · Scouting</h1><p>Rivales → Partidos analizados → fases del partido con pizarras, clips y comentarios staff.</p></header>
<div class="wrap">
  <aside class="side">
    <div class="side-head"><span>Equipos rivales</span><span class="badge">Listo</span></div>
    <div id="rivalList"></div>
    <div class="add-row"><input id="newRival" placeholder="Nombre del rival"><button onclick="addRival()">+ Añadir rival</button></div>
  </aside>
  <main class="main">
    <span class="crumb">Rivales</span> › <span class="crumb" id="crumbName">-</span>
    <h2 id="title">Selecciona un rival</h2>
    <button class="delete" onclick="deleteCurrent()">Eliminar rival</button>
    <section class="card"><div class="card-title"><span>Plantilla rival</span><span class="badge" id="playerCount">0 jugadoras</span></div><div class="card-body"><div class="player-list" id="players"></div><div class="form-line"><input id="dorsal" placeholder="Dorsal"><input id="playerName" placeholder="Nombre jugadora"><input id="position" placeholder="Posición"><button onclick="addPlayer()">+ Añadir</button></div></div></section>
    <section class="card"><div class="card-title"><span>Partidos analizados</span><span class="badge" id="matchCount">0 partidos</span></div><div class="card-body"><div class="match-list" id="matches"></div><div class="match-line"><input id="opponent" placeholder="Ej: vs Sakura FC"><input id="date" placeholder="Fecha"><input id="competition" placeholder="Competición/Jornada"><input id="result" placeholder="Resultado"><button onclick="addMatch()">+ Nuevo partido</button></div></div></section>
    <section class="card"><div class="card-title">Notas generales rival</div><div class="card-body"><textarea id="notes" placeholder="Notas generales..." onblur="saveNotes()"></textarea></div></section>
  </main>
</div>
<script>
let rivals=[], currentId=null;
async function load(){rivals=await fetch('/api/rivals').then(r=>r.json()); if(!currentId&&rivals.length)currentId=rivals[0].id; render();}
function current(){return rivals.find(r=>r.id===currentId)}
function render(){const list=document.getElementById('rivalList');list.innerHTML='';rivals.forEach(r=>{const b=document.createElement('button');b.className='rival-btn '+(r.id===currentId?'active':'');b.innerHTML=`<strong>${r.name}</strong><span>${r.matches.length} partidos · ${r.players.length} jugadoras</span>`;b.onclick=()=>{currentId=r.id;render()};list.appendChild(b)});const r=current(); if(!r)return;title.textContent=r.name;crumbName.textContent=r.name;playerCount.textContent=r.players.length+' jugadoras';matchCount.textContent=r.matches.length+' partidos';players.innerHTML=r.players.length?r.players.map(p=>`<div><b>${p.dorsal||''}</b> ${p.name} <span class="muted">${p.position||''}</span></div>`).join(''):'<div class="empty muted">Aún no hay jugadoras creadas.</div>';matches.innerHTML=r.matches.length?r.matches.map(m=>`<div><b>${m.opponent}</b> · ${m.date||''} · ${m.competition||''} · ${m.result||''}</div>`).join(''):'<div class="empty muted">Aún no hay partidos analizados.</div>';notes.value=r.notes||'';}
async function addRival(){const name=newRival.value.trim();if(!name)return;const r=await fetch('/api/rivals',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name})}).then(r=>r.json());newRival.value='';currentId=r.id;load();}
async function deleteCurrent(){if(!currentId)return;await fetch('/api/rivals/'+currentId,{method:'DELETE'});currentId=null;load();}
async function addPlayer(){const r=current();if(!r||!playerName.value.trim())return;await fetch(`/api/rivals/${r.id}/players`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({dorsal:dorsal.value,name:playerName.value,position:position.value})});dorsal.value=playerName.value=position.value='';load();}
async function addMatch(){const r=current();if(!r||!opponent.value.trim())return;await fetch(`/api/rivals/${r.id}/matches`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({opponent:opponent.value,date:date.value,competition:competition.value,result:result.value})});opponent.value=date.value=competition.value=result.value='';load();}
async function saveNotes(){const r=current();if(!r)return;await fetch(`/api/rivals/${r.id}/notes`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({notes:notes.value})});}
load();
</script>
</body></html>
"""
