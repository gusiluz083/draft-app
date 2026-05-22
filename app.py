from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path
import json
import uuid

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data.json"

app = FastAPI(title="Rivales - Scouting")


def load_data():
    if not DATA_FILE.exists():
        return {"rivals": [], "selected_id": None}
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"rivals": [], "selected_id": None}


def save_data(data):
    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


class RivalIn(BaseModel):
    name: str


class PlayerIn(BaseModel):
    dorsal: str = ""
    name: str
    position: str = ""


class MatchIn(BaseModel):
    title: str
    date: str = ""
    competition: str = ""
    result: str = ""


class NotesIn(BaseModel):
    notes: str = ""


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/data")
def api_data():
    data = load_data()
    if data["rivals"] and not data.get("selected_id"):
        data["selected_id"] = data["rivals"][0]["id"]
        save_data(data)
    return data


@app.post("/api/rivals")
def add_rival(payload: RivalIn):
    data = load_data()
    name = payload.name.strip()
    if not name:
        return JSONResponse({"error": "Nombre vacío"}, status_code=400)
    rival = {
        "id": str(uuid.uuid4()),
        "name": name,
        "players": [],
        "matches": [],
        "notes": "",
    }
    data["rivals"].append(rival)
    data["selected_id"] = rival["id"]
    save_data(data)
    return rival


@app.delete("/api/rivals/{rival_id}")
def delete_rival(rival_id: str):
    data = load_data()
    data["rivals"] = [r for r in data["rivals"] if r["id"] != rival_id]
    data["selected_id"] = data["rivals"][0]["id"] if data["rivals"] else None
    save_data(data)
    return data


@app.post("/api/rivals/{rival_id}/players")
def add_player(rival_id: str, payload: PlayerIn):
    data = load_data()
    for rival in data["rivals"]:
        if rival["id"] == rival_id:
            player = {
                "id": str(uuid.uuid4()),
                "dorsal": payload.dorsal.strip(),
                "name": payload.name.strip(),
                "position": payload.position.strip(),
            }
            if not player["name"]:
                return JSONResponse({"error": "Nombre de jugadora vacío"}, status_code=400)
            rival["players"].append(player)
            save_data(data)
            return player
    return JSONResponse({"error": "Rival no encontrado"}, status_code=404)


@app.post("/api/rivals/{rival_id}/matches")
def add_match(rival_id: str, payload: MatchIn):
    data = load_data()
    for rival in data["rivals"]:
        if rival["id"] == rival_id:
            match = {
                "id": str(uuid.uuid4()),
                "title": payload.title.strip(),
                "date": payload.date.strip(),
                "competition": payload.competition.strip(),
                "result": payload.result.strip(),
            }
            if not match["title"]:
                return JSONResponse({"error": "Partido vacío"}, status_code=400)
            rival["matches"].append(match)
            save_data(data)
            return match
    return JSONResponse({"error": "Rival no encontrado"}, status_code=404)


@app.post("/api/rivals/{rival_id}/notes")
def save_notes(rival_id: str, payload: NotesIn):
    data = load_data()
    for rival in data["rivals"]:
        if rival["id"] == rival_id:
            rival["notes"] = payload.notes
            save_data(data)
            return {"ok": True}
    return JSONResponse({"error": "Rival no encontrado"}, status_code=404)


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return HTML


HTML = r"""
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Rivales - Scouting</title>
<style>
:root{--dark:#06122e;--blue:#35b8ee;--line:#d6e1f2;--soft:#f6f9ff;--text:#06122e;--muted:#47607f;--green:#d9fff0;--red:#ffd8d8}
*{box-sizing:border-box} body{margin:0;font-family:Inter,Arial,sans-serif;background:#eef3f9;color:var(--text)}
.wrap{padding:26px}.hero{background:linear-gradient(90deg,#35b8ee,#111b4e,#020719);border-radius:24px;color:white;padding:18px 22px;display:flex;justify-content:space-between;align-items:center;box-shadow:0 18px 34px #0002}.hero h1{margin:0;font-size:34px}.hero p{margin:4px 0 0;font-size:13px}.topbtns button{margin-left:8px;border:1px solid #ffffff33;background:#ffffff18;color:white;border-radius:10px;padding:10px 14px;font-weight:800}.topbtns button:last-child{background:#fff;color:#001033}
.layout{display:grid;grid-template-columns:224px 1fr;gap:14px;margin-top:16px}.side{background:white;border-radius:18px;padding:10px;box-shadow:0 12px 28px #0001}.sideHead{display:flex;justify-content:space-between;align-items:center;font-weight:900;margin:4px 2px 12px}.pill{font-size:11px;background:var(--green);border-radius:99px;padding:7px 10px;color:#007a55;font-weight:900}.rivalList{display:flex;flex-direction:column;gap:8px;max-height:430px;overflow:auto}.rivalItem{width:100%;border:1px solid var(--line);background:#f8fafc;color:#06122e;border-radius:11px;padding:11px 10px;text-align:left;font-weight:900;cursor:pointer;opacity:1}.rivalItem:hover{background:#eaf2ff}.rivalItem.active{background:#06122e;color:white;border-color:#06122e}.rivalItem span{font-size:11px;opacity:.9}.addRival{display:flex;flex-direction:column;gap:8px;margin-top:12px}.input,textarea{border:1px solid var(--line);border-radius:10px;padding:10px;background:white;color:#06122e}button.primary{background:#06122e;color:white;border:0;border-radius:10px;padding:10px 14px;font-weight:900;cursor:pointer}.main h2{margin:6px 0 4px;font-size:24px}.crumb{font-size:12px;font-weight:900;background:#e8f1ff;border-radius:99px;padding:8px 12px;display:inline-block;margin-bottom:10px}.card{background:white;border:1px solid var(--line);border-radius:18px;margin:10px 0;overflow:hidden}.cardHead{display:flex;justify-content:space-between;align-items:center;padding:13px 14px;border-bottom:1px solid #e7eef9;font-weight:900}.cardBody{padding:12px}.row{display:flex;gap:8px}.row .grow{flex:1}.danger{background:var(--red);color:#b50000;border:0;border-radius:10px;padding:9px 12px;font-weight:900}.smallList{background:#f7fbff;border:1px solid var(--line);border-radius:12px;margin-bottom:10px;padding:10px}.empty{font-size:12px;color:var(--muted)}.itemLine{display:flex;justify-content:space-between;border-bottom:1px solid #edf2fa;padding:8px 0;font-size:13px}.itemLine:last-child{border-bottom:0}@media(max-width:800px){.layout{grid-template-columns:1fr}.hero{display:block}.topbtns{margin-top:12px}.row{flex-direction:column}}
</style>
</head>
<body><div class="wrap"><div class="hero"><div><h1>Rivales · Scouting</h1><p>Rivales → Partidos analizados → fases del partido con pizarras, clips y comentarios staff.</p></div><div class="topbtns"><button>Módulos</button><button>Draft</button><button>Tryouts</button><button>Guardar todo</button></div></div><div class="layout"><aside class="side"><div class="sideHead">Equipos rivales <span class="pill">Listo</span></div><div id="rivalList" class="rivalList"></div><div class="addRival"><input id="newRival" class="input" placeholder="Nombre del rival"><button class="primary" onclick="addRival()">+ Añadir rival</button></div></aside><main class="main"><div id="crumb" class="crumb">Rivales</div><div style="display:flex;justify-content:space-between;align-items:center"><h2 id="title">Sin rival seleccionado</h2><button class="danger" onclick="deleteSelected()">Eliminar rival</button></div><section class="card"><div class="cardHead">Plantilla rival <span id="playerCount" class="pill">0 jugadoras</span></div><div class="cardBody"><div class="smallList"><b>Ver / editar jugadoras creadas</b><div id="players"></div></div><div class="row"><input id="dorsal" class="input" placeholder="Dorsal" style="max-width:90px"><input id="playerName" class="input grow" placeholder="Nombre jugadora"><input id="position" class="input" placeholder="Posición" style="max-width:160px"><button class="primary" onclick="addPlayer()">+ Añadir</button></div></div></section><section class="card"><div class="cardHead">Partidos analizados <span id="matchCount" class="pill">0 partidos</span></div><div class="cardBody"><div id="matches" class="smallList"></div><div class="row"><input id="matchTitle" class="input grow" placeholder="Ej: vs Sakura FC"><input id="matchDate" class="input" placeholder="Fecha"><input id="competition" class="input" placeholder="Competición/Jornada"><input id="result" class="input" placeholder="Resultado"><button class="primary" onclick="addMatch()">+ Nuevo partido</button></div></div></section><section class="card"><div class="cardHead">Notas generales rival</div><div class="cardBody"><textarea id="notes" style="width:100%;height:72px" placeholder="Notas generales..."></textarea></div></section></main></div></div><script>
let state={rivals:[],selected_id:null};
async function api(url,opts={}){const r=await fetch(url,{headers:{'Content-Type':'application/json'},...opts}); if(!r.ok){alert((await r.json()).error||'Error'); throw new Error('api')} return r.json()}
function selected(){return state.rivals.find(r=>r.id===state.selected_id)||state.rivals[0]}
async function load(){state=await api('/api/data'); render()}
function render(){const list=document.getElementById('rivalList'); list.innerHTML=''; state.rivals.forEach(r=>{const b=document.createElement('button'); b.className='rivalItem '+(r.id===state.selected_id?'active':''); b.innerHTML=`${r.name}<br><span>${r.matches.length} partidos · ${r.players.length} jugadoras</span>`; b.onclick=()=>{state.selected_id=r.id; render()}; list.appendChild(b)}); const r=selected(); if(!r){document.getElementById('title').textContent='Sin rival seleccionado'; document.getElementById('crumb').textContent='Rivales'; return} document.getElementById('title').textContent=r.name; document.getElementById('crumb').textContent='Rivales › '+r.name; document.getElementById('playerCount').textContent=r.players.length+' jugadoras'; document.getElementById('matchCount').textContent=r.matches.length+' partidos'; document.getElementById('players').innerHTML=r.players.length?r.players.map(p=>`<div class="itemLine"><b>${p.dorsal?('#'+p.dorsal+' '):''}${p.name}</b><span>${p.position||''}</span></div>`).join(''):'<p class="empty">Aún no hay jugadoras creadas.</p>'; document.getElementById('matches').innerHTML=r.matches.length?r.matches.map(m=>`<div class="itemLine"><b>${m.title}</b><span>${[m.date,m.competition,m.result].filter(Boolean).join(' · ')}</span></div>`).join(''):'<p class="empty">Aún no hay partidos analizados.</p>'; document.getElementById('notes').value=r.notes||''}
async function addRival(){const name=document.getElementById('newRival').value; await api('/api/rivals',{method:'POST',body:JSON.stringify({name})}); document.getElementById('newRival').value=''; await load()}
async function deleteSelected(){const r=selected(); if(!r||!confirm('¿Eliminar rival?'))return; await api('/api/rivals/'+r.id,{method:'DELETE'}); await load()}
async function addPlayer(){const r=selected(); if(!r)return; await api(`/api/rivals/${r.id}/players`,{method:'POST',body:JSON.stringify({dorsal:dorsal.value,name:playerName.value,position:position.value})}); dorsal.value=playerName.value=position.value=''; await load()}
async function addMatch(){const r=selected(); if(!r)return; await api(`/api/rivals/${r.id}/matches`,{method:'POST',body:JSON.stringify({title:matchTitle.value,date:matchDate.value,competition:competition.value,result:result.value})}); matchTitle.value=matchDate.value=competition.value=result.value=''; await load()}
document.getElementById('notes').addEventListener('change',async()=>{const r=selected(); if(r) await api(`/api/rivals/${r.id}/notes`,{method:'POST',body:JSON.stringify({notes:notes.value})})});
load();
</script></body></html>
"""
