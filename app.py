import streamlit as st
from PIL import Image
from streamlit_js_eval import get_geolocation
import ia_engine
import html_generator
import google_drive_manager
import location_manager
import os

# -------------------------------------------------
# 1. CONFIGURACIÓN
# -------------------------------------------------
st.set_page_config(page_title="Tasador Agrícola", page_icon="🚜", layout="centered")

# CSS Limpio
st.markdown("""
<style>
    /* 1. Desaparece todo lo de Streamlit */
    header[data-testid="stHeader"] { display: none !important; }
    [data-testid="stToolbar"] { display: none !important; }
    footer { display: none !important; }
    
    /* 2. CONTENEDOR PRINCIPAL: EL TRUCO DEL ALMENDRUCO */
    .block-container { 
        /* Con padding-top: 0 a veces no basta. */
        /* Forzamos un margen negativo para 'chupar' el contenido hacia arriba */
        margin-top: -3rem !important; 
        
        padding-top: 0rem !important; 
        padding-bottom: 2rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    
    /* 3. LOGO */
    [data-testid="stImage"] { 
        display: flex; 
        justify-content: center;
        /* Aseguramos que la imagen no tenga margen propio */
        margin-top: 0 !important; 
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# 2. LÓGICA DE UBICACIÓN (Formato ID Puro)
# -------------------------------------------------
loc = get_geolocation(component_key="gps_id_verify")
texto_ubicacion = "PENDIENTE"

if loc and isinstance(loc, dict) and 'coords' in loc:
    lat = loc['coords']['latitude']
    lon = loc['coords']['longitude']
    # Esto ahora devuelve SOLO el código Base64 (Ej: NDEuMjMsLTUuNTU=)
    texto_ubicacion = location_manager.codificar_coordenadas(lat, lon)

# -------------------------------------------------
# 3. CONEXIÓN GOOGLE
# -------------------------------------------------
if "vertex_client" not in st.session_state:
    try:
        creds = dict(st.secrets["google"])
        st.session_state.vertex_client = ia_engine.conectar_vertex(creds)
    except Exception as e:
        st.error(f"Error credenciales: {e}")

# -------------------------------------------------
# 4. INTERFAZ (LOGO BLINDADO)
# -------------------------------------------------
# Si el archivo está, lo usa. Si no, usa la URL. Si falla todo, pone texto.
if os.path.exists("afoto.png"):
    st.image("afoto.png", width=300)
else:
    try:
        st.image("https://raw.githubusercontent.com/victorcasascanada2-beep/Tasacion1.0Beta/main/afoto.png", width=300)
    except:
        st.warning("⚠️ Logo no cargado, pero sistema operativo.")

st.title("Tasación Experta")

# -------------------------------------------------
# 5. FORMULARIO
# -------------------------------------------------
if "informe_final" not in st.session_state:
    with st.form("form_tasacion"):
        c1, c2 = st.columns(2)
        with c1:
            marca = st.text_input("Marca")
            modelo = st.text_input("Modelo")
        with c2:
            anio = st.text_input("Año", value="2018")
            horas = st.text_input("Horas", value="5000")
        
        obs = st.text_area("Observaciones")
        fotos = st.file_uploader("Fotos", accept_multiple_files=True, type=['jpg','png'])
        
        submit = st.form_submit_button("🚀 TASAR")

    if submit:
        if marca and modelo and fotos:
            with st.spinner("Generando ID y Tasación..."):
                # Aquí la IA recibe las coordenadas codificadas dentro del ID
                notas_ia = f"{obs}\n\n[ID_VERIFICACIÓN: {texto_ubicacion}]"
                
                try:
                    inf = ia_engine.realizar_peritaje(
                        st.session_state.vertex_client,
                        marca, modelo, int(anio), int(horas),
                        notas_ia, fotos
                    )
                    
                    st.session_state.informe_final = inf
                    st.session_state.fotos_final = [Image.open(f) for f in fotos]
                    st.session_state.marca = marca
                    st.session_state.modelo = modelo
                    # Generamos HTML con el ID limpio
                    st.session_state.html = html_generator.generar_informe_html(
                        marca, modelo, inf, st.session_state.fotos_final, texto_ubicacion
                    )
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

# -------------------------------------------------
# 6. RESULTADOS
# -------------------------------------------------
if "informe_final" in st.session_state:
    st.markdown(st.session_state.informe_final)
    
    # En el HTML saldrá: ID_VERIFICACIÓN: <Tus_Coordenadas_B64>
    st.download_button("📥 PDF/HTML", st.session_state.html, file_name="tasacion.html")
    
    if st.button("🔄 NUEVA"):
        st.session_state.clear()
        st.rerun()
