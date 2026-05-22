import streamlit as st

st.set_page_config(page_title="DraftManager - Pizarras", layout="wide")

st.title("📋 DraftManager · Pizarras")

menu = st.sidebar.selectbox(
    "Selecciona una pizarra",
    [
        "1vs1",
        "2vs2",
        "3vs3",
        "4vs4",
        "5vs5",
        "6vs6",
        "DADO 1vs1 Reina",
        "DADO 1vs1 Portera",
        "DADO 2vs2",
        "DADO 3vs3"
    ]
)

st.header(menu)

st.info("Sube una imagen llamada 'campo.png' a la misma carpeta para visualizar el campo.")

try:
    st.image("campo.png", use_container_width=True)
except:
    st.warning("No se encontró campo.png")

st.markdown("## Fichas tácticas")

if "fichas" not in st.session_state:
    st.session_state.fichas = {}

if menu not in st.session_state.fichas:
    st.session_state.fichas[menu] = []

with st.form(f"add_player_{menu}", clear_on_submit=True):
    c1, c2 = st.columns([5,1])

    with c1:
        nombre = st.text_input("Nombre de la ficha")

    with c2:
        añadir = st.form_submit_button("➕ Añadir")

    if añadir and nombre.strip():
        st.session_state.fichas[menu].append(nombre.strip())
        st.rerun()

st.markdown("---")

for i, ficha in enumerate(st.session_state.fichas[menu]):
    col1, col2 = st.columns([8,1])

    with col1:
        st.text_input(
            f"Ficha {i+1}",
            value=ficha,
            key=f"{menu}_{i}"
        )

    with col2:
        if st.button("❌", key=f"delete_{menu}_{i}"):
            st.session_state.fichas[menu].pop(i)
            st.rerun()

st.markdown("---")
st.success("Pizarra preparada para trabajar tácticamente.")
