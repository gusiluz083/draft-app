import json
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components

DATA_FILE = Path('rivales_scouting_data.json')

st.set_page_config(page_title='DraftManager · Rivales y Pizarras', layout='wide')

CSS = '''
<style>
.stApp { background: #f4f7fb; }
.header {
    background: linear-gradient(90deg, #36b4e5, #09112c);
    color: white; padding: 22px; border-radius: 22px; margin-bottom: 16px;
}
.header h1 { margin: 0; font-size: 34px; }
.header p { margin: 4px 0 0 0; font-size: 13px; }
.sidebar-box {
    background: white; border-radius: 18px; padding: 14px;
    box-shadow: 0 10px 30px rgba(15,23,42,.08);
}
.card {
    background: white; border: 1px solid #d9e4f5; border-radius: 18px;
    padding: 14px; margin-bottom: 14px;
}
.badge { background:#d8fff0; color:#00875a; border-radius:999px; padding:6px 10px; font-size:12px; font-weight:800; }
.board-help { color:#475569; font-size:14px; margin-top:-6px; }
</style>
'''
st.markdown(CSS, unsafe_allow_html=True)

BOARDS = [
    ('1vs1', '1 vs 1'),
    ('2vs2', '2 vs 2'),
    ('3vs3', '3 vs 3'),
    ('4vs4', '4 vs 4'),
    ('5vs5', '5 vs 5'),
    ('6vs6', '6 vs 6'),
    ('dado_1vs1_reina', 'DADO · 1 vs 1 Reina'),
    ('dado_1vs1_portera', 'DADO · 1 vs 1 Portera'),
    ('dado_2vs2', 'DADO · 2 vs 2'),
    ('dado_3vs3', 'DADO · 3 vs 3'),
]

def load_data():
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text(encoding='utf-8'))
        except Exception:
            pass
    return {'rivals': [], 'selected_id': None}

def save_data(data):
    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

def new_id(data):
    existing = [r.get('id', 0) for r in data['rivals']]
    return (max(existing) + 1) if existing else 1

def render_board(board_key, board_title):
    storage_key = f'draftmanager_pizarra_{board_key}'
    html = f'''
<!doctype html>
<html>
<head>
<meta charset="utf-8" />
<style>
  body {{ margin:0; font-family: Arial, sans-serif; background:#f4f7fb; }}
  .wrap {{ width:100%; }}
  .toolbar {{
    display:flex; gap:10px; flex-wrap:wrap; align-items:center;
    background:#ffffff; border:1px solid #d9e4f5; border-radius:16px;
    padding:12px; margin-bottom:10px;
  }}
  input {{ height:38px; border:1px solid #cbd5e1; border-radius:10px; padding:0 10px; min-width:220px; font-weight:700; }}
  button {{ height:38px; border:0; border-radius:10px; padding:0 14px; font-weight:800; cursor:pointer; }}
  .primary {{ background:#06122e; color:white; }}
  .secondary {{ background:#e2e8f0; color:#06122e; }}
  .danger {{ background:#fee2e2; color:#991b1b; }}
  .hint {{ color:#64748b; font-size:13px; font-weight:700; }}
  #board {{
    position:relative; width:100%; height:700px; min-width:900px;
    background:linear-gradient(90deg,#7b7d7c 0 16.66%,#4f5152 16.66% 33.33%,#7b7d7c 33.33% 50%,#4f5152 50% 66.66%,#7b7d7c 66.66% 83.33%,#4f5152 83.33% 100%);
    border:18px solid #3f4142; border-radius:14px; overflow:hidden;
    box-shadow:0 18px 45px rgba(15,23,42,.18);
  }}
  .line {{ position:absolute; border-color:white; border-style:solid; opacity:.96; box-sizing:border-box; }}
  .outer {{ left:4%; top:7%; width:92%; height:86%; border-width:3px; }}
  .half {{ left:50%; top:7%; height:86%; border-left-width:3px; }}
  .center {{ left:39.5%; top:31%; width:21%; height:38%; border-width:3px; border-radius:50%; }}
  .spot {{ position:absolute; width:12px; height:12px; background:white; border-radius:50%; transform:translate(-50%,-50%); box-shadow:0 2px 8px rgba(0,0,0,.35); }}
  .boxL {{ left:4%; top:24%; width:23%; height:52%; border-width:3px; border-left-width:0; }}
  .boxR {{ right:4%; top:24%; width:23%; height:52%; border-width:3px; border-right-width:0; }}
  .goalL {{ left:4%; top:39%; width:8%; height:22%; border-width:3px; border-left-width:0; }}
  .goalR {{ right:4%; top:39%; width:8%; height:22%; border-width:3px; border-right-width:0; }}
  .arcL {{ left:23%; top:39%; width:9%; height:22%; border-width:3px; border-left:0; border-radius:0 100px 100px 0; }}
  .arcR {{ right:23%; top:39%; width:9%; height:22%; border-width:3px; border-right:0; border-radius:100px 0 0 100px; }}
  .token {{
    position:absolute; min-width:74px; height:42px; padding:0 12px;
    border-radius:999px; background:#06122e; color:#fff; border:3px solid #fff;
    display:flex; align-items:center; justify-content:center;
    font-size:14px; font-weight:900; cursor:grab; user-select:none;
    box-shadow:0 8px 20px rgba(0,0,0,.35); z-index:5;
  }}
  .token.team2 {{ background:#36b4e5; color:#06122e; }}
  .token.selected {{ outline:4px solid #facc15; }}
  .title {{ position:absolute; left:20px; top:14px; color:white; font-size:20px; font-weight:900; text-shadow:0 2px 8px #000; }}
</style>
</head>
<body>
<div class="wrap">
  <div class="toolbar">
    <input id="name" placeholder="Nombre de la ficha" />
    <button class="primary" onclick="addToken('team1')">+ Ficha negra</button>
    <button class="primary" onclick="addToken('team2')">+ Ficha azul</button>
    <button class="secondary" onclick="renameSelected()">Renombrar seleccionada</button>
    <button class="danger" onclick="deleteSelected()">Borrar seleccionada</button>
    <button class="danger" onclick="clearBoard()">Borrar pizarra</button>
    <span class="hint">Arrastra las fichas. Se guarda automáticamente en este navegador.</span>
  </div>
  <div id="board">
    <div class="title">{board_title}</div>
    <div class="line outer"></div><div class="line half"></div><div class="line center"></div>
    <div class="line boxL"></div><div class="line boxR"></div><div class="line goalL"></div><div class="line goalR"></div>
    <div class="line arcL"></div><div class="line arcR"></div>
    <div class="spot" style="left:50%;top:50%"></div><div class="spot" style="left:19%;top:50%"></div><div class="spot" style="left:81%;top:50%"></div>
  </div>
</div>
<script>
const storageKey = {json.dumps(storage_key)};
const board = document.getElementById('board');
let tokens = [];
let selectedId = null;
let dragging = null;
let dx = 0, dy = 0;

function save() {{ localStorage.setItem(storageKey, JSON.stringify(tokens)); }}
function load() {{
  try {{ tokens = JSON.parse(localStorage.getItem(storageKey) || '[]'); }} catch(e) {{ tokens = []; }}
  draw();
}}
function draw() {{
  document.querySelectorAll('.token').forEach(e => e.remove());
  tokens.forEach(t => {{
    const el = document.createElement('div');
    el.className = 'token ' + (t.team === 'team2' ? 'team2' : '') + (t.id === selectedId ? ' selected' : '');
    el.textContent = t.name;
    el.style.left = t.x + 'px';
    el.style.top = t.y + 'px';
    el.dataset.id = t.id;
    el.onmousedown = startDrag;
    el.onclick = (ev) => {{ ev.stopPropagation(); selectedId = t.id; draw(); }};
    board.appendChild(el);
  }});
}}
function addToken(team) {{
  const input = document.getElementById('name');
  const name = (input.value || 'Ficha').trim();
  tokens.push({{ id: Date.now().toString() + Math.random().toString(16).slice(2), name, team, x: board.clientWidth/2 - 40, y: board.clientHeight/2 - 20 }});
  input.value = '';
  save(); draw();
}}
function renameSelected() {{
  if (!selectedId) return alert('Selecciona una ficha primero.');
  const input = document.getElementById('name');
  const name = (input.value || '').trim();
  if (!name) return alert('Escribe el nuevo nombre en la caja.');
  tokens = tokens.map(t => t.id === selectedId ? {{...t, name}} : t);
  input.value = '';
  save(); draw();
}}
function deleteSelected() {{
  if (!selectedId) return alert('Selecciona una ficha primero.');
  tokens = tokens.filter(t => t.id !== selectedId);
  selectedId = null;
  save(); draw();
}}
function clearBoard() {{
  if (confirm('¿Borrar todas las fichas de esta pizarra?')) {{ tokens = []; selectedId = null; save(); draw(); }}
}}
function startDrag(ev) {{
  const id = ev.currentTarget.dataset.id;
  selectedId = id;
  dragging = id;
  const rect = ev.currentTarget.getBoundingClientRect();
  dx = ev.clientX - rect.left;
  dy = ev.clientY - rect.top;
  draw();
}}
document.addEventListener('mousemove', (ev) => {{
  if (!dragging) return;
  const br = board.getBoundingClientRect();
  tokens = tokens.map(t => {{
    if (t.id !== dragging) return t;
    let x = ev.clientX - br.left - dx;
    let y = ev.clientY - br.top - dy;
    x = Math.max(0, Math.min(board.clientWidth - 90, x));
    y = Math.max(0, Math.min(board.clientHeight - 50, y));
    return {{...t, x, y}};
  }});
  draw();
}});
document.addEventListener('mouseup', () => {{ if (dragging) {{ dragging = null; save(); }} }});
board.onclick = () => {{ selectedId = null; draw(); }};
load();
</script>
</body>
</html>
'''
    components.html(html, height=820, scrolling=True)

def rivales_module(data):
    left, main = st.columns([1.15, 6])
    with left:
        st.markdown('<div class="sidebar-box">', unsafe_allow_html=True)
        st.markdown('### Equipos rivales')
        st.markdown('<span class="badge">Listo</span>', unsafe_allow_html=True)
        if not data['rivals']:
            st.info('Aún no hay rivales creados.')
        for rival in data['rivals']:
            active = data.get('selected_id') == rival['id']
            partidos = len(rival.get('matches', []))
            jugadoras = len(rival.get('players', []))
            label = f"{'🟢 ' if active else ''}{rival['name']}\n• {partidos} partidos · {jugadoras} jugadoras"
            if st.button(label, key=f"select_{rival['id']}", use_container_width=True, type="primary" if active else "secondary"):
                data['selected_id'] = rival['id']
                save_data(data)
                st.rerun()
        with st.form('add_rival', clear_on_submit=True):
            name = st.text_input('Nombre del rival')
            submit = st.form_submit_button('+ Añadir rival', use_container_width=True)
            if submit and name.strip():
                rid = new_id(data)
                data['rivals'].append({'id': rid, 'name': name.strip(), 'players': [], 'matches': [], 'notes': ''})
                data['selected_id'] = rid
                save_data(data)
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    selected = next((r for r in data['rivals'] if r['id'] == data.get('selected_id')), None)
    with main:
        if not selected:
            st.warning('Crea o selecciona un rival para empezar.')
            return
        top1, top2 = st.columns([5, 1])
        with top1:
            st.caption('Rivales › ' + selected['name'])
            st.title(selected['name'])
        with top2:
            if st.button('Eliminar rival', type='secondary'):
                data['rivals'] = [r for r in data['rivals'] if r['id'] != selected['id']]
                data['selected_id'] = data['rivals'][0]['id'] if data['rivals'] else None
                save_data(data)
                st.rerun()

        st.markdown('<div class="card">', unsafe_allow_html=True)
        c1, c2 = st.columns([5, 1])
        c1.subheader('Plantilla rival')
        c2.markdown(f'<span class="badge">{len(selected.get("players", []))} jugadoras</span>', unsafe_allow_html=True)
        with st.expander('Ver / editar jugadoras creadas', expanded=True):
            if selected.get('players'):
                for i, p in enumerate(selected['players']):
                    a, b, c, d = st.columns([1, 4, 3, 1])
                    selected['players'][i]['number'] = a.text_input('Dorsal', value=p.get('number', ''), key=f'n_{i}')
                    selected['players'][i]['name'] = b.text_input('Nombre jugadora', value=p.get('name', ''), key=f'p_{i}')
                    selected['players'][i]['position'] = c.text_input('Posición', value=p.get('position', ''), key=f'pos_{i}')
                    if d.button('X', key=f'del_p_{i}'):
                        selected['players'].pop(i)
                        save_data(data)
                        st.rerun()
                if st.button('Guardar cambios plantilla'):
                    save_data(data)
                    st.success('Plantilla guardada')
            else:
                st.caption('No hay jugadoras creadas todavía.')
        with st.form('add_player', clear_on_submit=True):
            p1, p2, p3, p4 = st.columns([1, 6, 2, 1])
            number = p1.text_input('Dorsal')
            player_name = p2.text_input('Nombre jugadora')
            position = p3.text_input('Posición')
            add_player = p4.form_submit_button('+ Añadir')
            if add_player and player_name.strip():
                selected.setdefault('players', []).append({'number': number.strip(), 'name': player_name.strip(), 'position': position.strip()})
                save_data(data)
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="card">', unsafe_allow_html=True)
        m1, m2 = st.columns([5, 1])
        m1.subheader('Partidos analizados')
        m2.markdown(f'<span class="badge">{len(selected.get("matches", []))} partidos</span>', unsafe_allow_html=True)
        if selected.get('matches'):
            for m in selected['matches']:
                st.write(f"**{m.get('title','')}** · {m.get('date','')} · {m.get('competition','')} · {m.get('result','')}")
        else:
            st.caption('Aún no hay partidos analizados.')
        with st.form('add_match', clear_on_submit=True):
            x1, x2, x3, x4, x5 = st.columns([5, 1.2, 2, 1.2, 1.2])
            title = x1.text_input('Ej: vs Sakura FC')
            date = x2.text_input('Fecha')
            comp = x3.text_input('Competición/Jornada')
            result = x4.text_input('Resultado')
            add_match = x5.form_submit_button('+ Nuevo partido')
            if add_match and title.strip():
                selected.setdefault('matches', []).append({'title': title.strip(), 'date': date.strip(), 'competition': comp.strip(), 'result': result.strip()})
                save_data(data)
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader('Notas generales rival')
        selected['notes'] = st.text_area('Notas generales...', value=selected.get('notes', ''), height=120)
        if st.button('Guardar todo'):
            save_data(data)
            st.success('Todo guardado')
        st.markdown('</div>', unsafe_allow_html=True)

def pizarras_module():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader('Pizarras')
    st.markdown('<p class="board-help">Selecciona una pizarra, crea fichas con nombre, arrástralas y borra la ficha seleccionada cuando quieras. Cada pizarra conserva sus fichas en el navegador.</p>', unsafe_allow_html=True)
    board_key = st.selectbox('Selecciona pizarra', [k for k, _ in BOARDS], format_func=lambda k: dict(BOARDS)[k])
    st.markdown('</div>', unsafe_allow_html=True)
    render_board(board_key, dict(BOARDS)[board_key])

st.markdown('<div class="header"><h1>DraftManager</h1><p>Rivales, scouting y pizarras tácticas.</p></div>', unsafe_allow_html=True)

data = load_data()
module = st.sidebar.radio('Módulos', ['Rivales', 'Pizarras'], index=0)

if module == 'Rivales':
    rivales_module(data)
else:
    pizarras_module()
