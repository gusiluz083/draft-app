import json
from pathlib import Path
import streamlit as st

DATA_FILE = Path('rivales_scouting_data.json')

st.set_page_config(page_title='Rivales - Scouting', layout='wide')

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
.rival-card {
    display: block; width: 100%; padding: 12px 14px; margin: 8px 0;
    border-radius: 11px; border: 1px solid #d6e1f2;
    background: #f8fafc; color: #06122e !important;
    font-weight: 700; text-align: left;
}
.rival-card small { color: #475569 !important; font-weight: 600; }
.rival-card-active {
    background: #06122e !important; color: white !important; border-color: #06122e;
}
.rival-card-active small { color: white !important; }
.card {
    background: white; border: 1px solid #d9e4f5; border-radius: 18px;
    padding: 14px; margin-bottom: 14px;
}
.badge { background:#d8fff0; color:#00875a; border-radius:999px; padding:6px 10px; font-size:12px; font-weight:800; }
</style>
'''
st.markdown(CSS, unsafe_allow_html=True)

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

data = load_data()

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

        label = f"""
{'🟢 ' if active else ''}
{rival['name']}
• {partidos} partidos · {jugadoras} jugadoras
"""

        if st.button(
            label,
            key=f"select_{rival['id']}",
            use_container_width=True,
            type="primary" if active else "secondary"
        ):
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
    else:
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
