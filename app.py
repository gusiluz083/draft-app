import json
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components

DATA_FILE = Path('rivales_scouting_data.json')
PIZARRAS_FILE = Path('pizarras_data.json')

st.set_page_config(page_title='DraftManager', layout='wide')

CSS = """
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
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

PIZARRAS = [
    '1vs1', '2vs2', '3vs3', '4vs4', '5vs5', '6vs6',
    'DADO 1vs1 Reina', 'DADO 1vs1 Portera', 'DADO 2vs2', 'DADO 3vs3'
]


def load_json(path, default):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding='utf-8'))
        except Exception:
            pass
    return default


def save_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def new_id(data):
    existing = [r.get('id', 0) for r in data.get('rivals', [])]
    return (max(existing) + 1) if existing else 1


def render_rivales():
    data = load_json(DATA_FILE, {'rivals': [], 'selected_id': None})
    st.markdown('<div class="header"><h1>Rivales · Scouting</h1><p>Rivales → Partidos analizados → fases del partido con pizarras, clips y comentarios staff.</p></div>', unsafe_allow_html=True)
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
            if st.button(label, key=f"select_{rival['id']}", use_container_width=True, type='primary' if active else 'secondary'):
                data['selected_id'] = rival['id']
                save_json(DATA_FILE, data)
                st.rerun()
        with st.form('add_rival', clear_on_submit=True):
            name = st.text_input('Nombre del rival')
            submit = st.form_submit_button('+ Añadir rival', use_container_width=True)
            if submit and name.strip():
                rid = new_id(data)
                data['rivals'].append({'id': rid, 'name': name.strip(), 'players': [], 'matches': [], 'notes': ''})
                data['selected_id'] = rid
                save_json(DATA_FILE, data)
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
                save_json(DATA_FILE, data)
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
                        save_json(DATA_FILE, data)
                        st.rerun()
                if st.button('Guardar cambios plantilla'):
                    save_json(DATA_FILE, data)
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
                save_json(DATA_FILE, data)
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
                save_json(DATA_FILE, data)
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader('Notas generales rival')
        selected['notes'] = st.text_area('Notas generales...', value=selected.get('notes', ''), height=120)
        if st.button('Guardar todo'):
            save_json(DATA_FILE, data)
            st.success('Todo guardado')
        st.markdown('</div>', unsafe_allow_html=True)


def field_html(board_name, players):
    safe_board = json.dumps(board_name)
    safe_players = json.dumps(players, ensure_ascii=False)
    return f'''
<!DOCTYPE html><html><head><meta charset="UTF-8" />
<style>
body {{ margin:0; font-family: Arial, sans-serif; background: transparent; }}
.wrap {{ width: 100%; display:flex; justify-content:center; }}
.board {{ width: 1180px; height: 720px; position: relative; overflow:hidden; border-radius: 22px; background:#364044; border: 8px solid #20282b; box-shadow: 0 20px 50px rgba(15,23,42,.25); }}
.pitch {{ position:absolute; inset:24px; border:4px solid #f8fafc; }}
.mid {{ position:absolute; left:50%; top:24px; bottom:24px; border-left:4px solid #f8fafc; }}
.circle {{ position:absolute; width:210px; height:210px; left:calc(50% - 105px); top:calc(50% - 105px); border:4px solid #f8fafc; border-radius:50%; }}
.spot {{ position:absolute; width:12px; height:12px; background:#f8fafc; border-radius:50%; left:calc(50% - 6px); top:calc(50% - 6px); }}
.areaL, .areaR {{ position:absolute; top:145px; width:220px; height:430px; border:4px solid #f8fafc; }}
.areaL {{ left:24px; border-left:0; }} .areaR {{ right:24px; border-right:0; }}
.smallL, .smallR {{ position:absolute; top:260px; width:95px; height:200px; border:4px solid #f8fafc; }}
.smallL {{ left:24px; border-left:0; }} .smallR {{ right:24px; border-right:0; }}
.arcL, .arcR {{ position:absolute; top:275px; width:160px; height:160px; border:4px solid #f8fafc; border-radius:50%; }}
.arcL {{ left:160px; clip-path: inset(0 0 0 82px); }} .arcR {{ right:160px; clip-path: inset(0 82px 0 0); }}
.player {{ position:absolute; min-width:74px; min-height:74px; padding:10px; border-radius:50%; background: linear-gradient(145deg,#ffffff,#dbeafe); border:4px solid #06122e; color:#06122e; font-weight:900; font-size:13px; text-align:center; display:flex; align-items:center; justify-content:center; cursor:grab; user-select:none; box-shadow:0 12px 25px rgba(0,0,0,.25); z-index:20; }}
.player:active {{ cursor:grabbing; transform:scale(1.04); }}
.help {{ position:absolute; left:36px; top:34px; background:rgba(255,255,255,.9); color:#06122e; padding:7px 10px; border-radius:999px; font-size:12px; font-weight:800; z-index:10; }}
</style></head><body>
<div class="wrap"><div class="board" id="board">
<div class="pitch"></div><div class="mid"></div><div class="circle"></div><div class="spot"></div><div class="areaL"></div><div class="areaR"></div><div class="smallL"></div><div class="smallR"></div><div class="arcL"></div><div class="arcR"></div><div class="help">Arrastra las fichas y colócalas sobre el campo</div>
</div></div>
<script>
const boardName = {safe_board};
const players = {safe_players};
const board = document.getElementById('board');
const key = 'draftmanager_positions_' + boardName;
let positions = JSON.parse(localStorage.getItem(key) || '{{}}');
function save() {{ localStorage.setItem(key, JSON.stringify(positions)); }}
function defaultPos(i) {{ return {{x: 70 + (i%6)*110, y: 80 + Math.floor(i/6)*100}}; }}
players.forEach((p, i) => {{
  const el = document.createElement('div');
  el.className = 'player'; el.innerText = p; el.dataset.name = p;
  const pos = positions[p] || defaultPos(i);
  el.style.left = pos.x + 'px'; el.style.top = pos.y + 'px';
  board.appendChild(el);
  let dragging=false, sx=0, sy=0, ox=0, oy=0;
  el.addEventListener('pointerdown', (e) => {{ dragging=true; el.setPointerCapture(e.pointerId); sx=e.clientX; sy=e.clientY; ox=parseFloat(el.style.left); oy=parseFloat(el.style.top); }});
  el.addEventListener('pointermove', (e) => {{ if(!dragging) return; let nx=ox+e.clientX-sx; let ny=oy+e.clientY-sy; nx=Math.max(0, Math.min(board.clientWidth-el.offsetWidth, nx)); ny=Math.max(0, Math.min(board.clientHeight-el.offsetHeight, ny)); el.style.left=nx+'px'; el.style.top=ny+'px'; }});
  el.addEventListener('pointerup', () => {{ dragging=false; positions[p]={{x:parseFloat(el.style.left), y:parseFloat(el.style.top)}}; save(); }});
}});
</script></body></html>
'''


def render_pizarras():
    pdata = load_json(PIZARRAS_FILE, {'boards': {name: {'players': []} for name in PIZARRAS}})
    for name in PIZARRAS:
        pdata.setdefault('boards', {}).setdefault(name, {'players': []})
    st.markdown('<div class="header"><h1>Pizarras tácticas</h1><p>Campos grandes para trabajar situaciones de juego y DADO.</p></div>', unsafe_allow_html=True)
    left, main = st.columns([1.25, 6])
    with left:
        st.markdown('<div class="sidebar-box">', unsafe_allow_html=True)
        st.markdown('### Pizarras')
        board = st.radio('Selecciona', PIZARRAS, label_visibility='collapsed')
        st.markdown('</div>', unsafe_allow_html=True)
    with main:
        board_data = pdata['boards'][board]
        players = board_data.setdefault('players', [])
        st.caption('DraftManager › Pizarras')
        st.title(board)
        c1, c2, c3 = st.columns([3, 1, 1])
        with c1:
            with st.form(f'add_token_{board}', clear_on_submit=True):
                nombre = st.text_input('Nombre de la ficha / jugadora')
                submitted = st.form_submit_button('➕ Añadir ficha')
                if submitted and nombre.strip():
                    players.append(nombre.strip())
                    save_json(PIZARRAS_FILE, pdata)
                    st.rerun()
        with c2:
            st.metric('Fichas', len(players))
        with c3:
            if st.button('🧹 Borrar todas', use_container_width=True):
                players.clear()
                save_json(PIZARRAS_FILE, pdata)
                st.rerun()
        if players:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader('Fichas creadas')
            for i, p in enumerate(list(players)):
                a, b = st.columns([6, 1])
                new_name = a.text_input('Nombre', value=p, key=f'edit_{board}_{i}')
                if new_name != p and new_name.strip():
                    players[i] = new_name.strip()
                    save_json(PIZARRAS_FILE, pdata)
                if b.button('Borrar', key=f'del_{board}_{i}'):
                    players.pop(i)
                    save_json(PIZARRAS_FILE, pdata)
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info('Añade fichas arriba. Después podrás arrastrarlas dentro del campo.')
        components.html(field_html(board, players), height=760, scrolling=False)
        st.caption('Las posiciones se guardan en este navegador para cada pizarra. Las fichas se guardan en pizarras_data.json.')


with st.sidebar:
    st.title('DraftManager')
    modulo = st.radio('Módulo', ['Rivales / Scouting', 'Pizarras'], label_visibility='collapsed')

if modulo == 'Rivales / Scouting':
    render_rivales()
else:
    render_pizarras()
