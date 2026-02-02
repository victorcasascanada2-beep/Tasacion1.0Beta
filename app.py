import streamlit as st
from PIL import Image
import ia_engine
import html_generator
import google_drive_manager
import location_manager
import time
from streamlit_js_eval import get_geolocation

# -------------------------------------------------
# 1. CONFIGURACIÓN DE PÁGINA
# -------------------------------------------------
st.set_page_config(
    page_title="Tasador Agrícola",
    page_icon="🚜",
    layout="centered"
)

# -------------------------------------------------
# 2. CSS PERSONALIZADO (Logo centrado y limpieza)
# -------------------------------------------------
st.markdown("""
<style>
    [data-testid="stToolbar"], footer {display: none;}
    section[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] {display: none !important;}
    
    /* Bajamos el contenido para que el logo respire */
    .block-container { padding-top: 5rem !important; }
    
    /* Centrado de logo */
    [data-testid="stImage"] {
        display: flex;
        justify-content: center;
    }
    
    .stSpinner > div { border-top-color: #2e7d32 !important; }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# 3. GESTIÓN DE UBICACIÓN (El motor de ayer)
# -------------------------------------------------
# Disparamos el GPS nada más entrar
if "geo_data" not in st.session_state:
    st.session_state.geo_data = None

# Intentamos capturar coordenadas (esto lanza el permiso azul del Maps)
coords = get_geolocation(component_key="gps_disparo_agricola")

if coords and "coords" in coords:
    st.session_state.geo_data = (coords["coords"]["latitude"], coords["coords"]["longitude"])

# Convertimos a Base64 (pueblo o fallback)
# Esto es lo que usaremos para la IA y el RefDoc
texto_ubicacion = location_manager.obtener_ubicacion_final(st.session_state.geo_data)

# -------------------------------------------------
# 4. CONEXIÓN VERTEX
# -------------------------------------------------
if "vertex_client" not in st.session_state:
    try:
        creds = dict(st.secrets["google"])
        st.session_state.vertex_client = ia_engine.conectar_vertex(creds)
    except Exception as e:
        st.error(f"Error de credenciales: {e}")

# -------------------------------------------------
# 5. CABECERA
# -------------------------------------------------
logo_url = "https://raw.githubusercontent.com/victorcasascanada2-beep/CopiaPruebaClave/3e79639d3faf452777931d392257eef8ed8c6144/afoto.png"
st.image(logo_url, width=300)
st.title("Tasación Experta")
st.caption("Ajustando valores según mercado local de peritaje.")
st.divider()

# -------------------------------------------------
# 6. FORMULARIO DE TASACIÓN
# -------------------------------------------------
if "informe_final" not in st.session_state:
    with st.form("form_tasacion"):
        col1, col2 = st.columns(2)
        with col1:
            marca = st.text_input("Marca", placeholder="John Deere")
            modelo = st.text_input("Modelo", placeholder="6155R")
        with col2:
            anio_txt = st.text_input("Año", value="2018")
            horas_txt = st.text_input("Horas", value="5000")
        
        observaciones = st.text_area("Notas / Extras (Pala, Tripuntal, etc.)")
        fotos = st.file_uploader("Fotos del tractor", accept_multiple_files=True, type=['jpg', 'jpeg', 'png'])
        
        submit = st.form_submit_button("🚀 REALIZAR TASACIÓN", use_container_width=True)

    if submit:
        if not (marca and modelo and fotos):
            st.warning("⚠️ Por favor, rellena marca, modelo y sube las fotos.")
        else:
            with st.spinner("Analizando mercado local y estado visual..."):
                try:
                    # Inyectamos la ubicación codificada de forma interna para la IA
                    # (La IA usará el pueblo real si está en el Base64)
                    notas_ia = f"{observaciones}\n\n[REF_GEO: {texto_ubicacion}]"
                    
                    inf = ia_engine.realizar_peritaje(
                        st.session_state.vertex_client, 
                        marca, modelo, int(anio_txt), int(horas_txt), 
                        notas_ia, fotos
                    )
                    
                    # Guardamos resultados
                    st.session_state.informe_final = inf
                    st.session_state.fotos_final = [Image.open(f) for f in fotos]
                    st.session_state.marca_final, st.session_state.modelo_final = marca, modelo
                    
                    # Generamos el HTML (con el motor de tablas y fotos ligeras)
                    st.session_state.html_listo = html_generator.generar_informe_html(
                        marca, modelo, inf, st.session_state.fotos_final, texto_ubicacion
                    )
                    
                    st.rerun()
                except Exception as e:
                    st.error(f"Error técnico: {e}")

# -------------------------------------------------
# 7. RESULTADOS Y DESCARGA
# -------------------------------------------------
if "informe_final" in st.session_state:
    # Muestra el informe en la app (Streamlit ya formatea bien las tablas aquí)
    st.markdown(st.session_state.informe_final)
    
    with st.expander("Ver imágenes analizadas"):
        cols = st.columns(3)
        for idx, img in enumerate(st.session_state.fotos_final):
            cols[idx % 3].image(img, use_container_width=True)

    st.divider()
    
    # BOTONES DE ACCIÓN
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.download_button(
            "📥 DESCARGAR", 
            data=st.session_state.html_listo, 
            file_name=f"tasacion_{st.session_state.modelo_final}.html", 
            mime="text/html",
            use_container_width=True
        )
    
    with c2:
        if st.button("☁️ DRIVE", use_container_width=True):
            with st.spinner("Subiendo..."):
                creds_drive = dict(st.secrets["google"])
                nombre = f"Tasacion_{st.session_state.marca_final}_{st.session_state.modelo_final}.html"
                exito = google_drive_manager.subir_informe(creds_drive, nombre, st.session_state.html_listo)
                if exito: st.success("✅ Guardado en Drive")
                else: st.error("❌ Error al subir")
    
    with c3:
        if st.button("🔄 NUEVA", use_container_width=True):
            for k in ["informe_final", "fotos_final", "marca_final", "modelo_final", "html_listo"]:
                if k in st.session_state: del st.session_state[k]
            st.rerun()
