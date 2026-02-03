import streamlit as st
from PIL import Image
from streamlit_js_eval import get_geolocation
import ia_engine
import html_generator
import google_drive_manager
import location_manager
import os

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Tasador Agrícola", page_icon="🚜", layout="centered")

# 2. CSS "MODO APP NATIVA"
st.markdown("""
<style>
    header[data-testid="stHeader"] { display: none !important; }
    [data-testid="stToolbar"] { display: none !important; }
    footer { display: none !important; }
    .block-container { 
        margin-top: -3rem !important;
        padding-top: 1rem !important;
        padding-bottom: 3rem !important;
    }
    [data-testid="stImage"] { display: flex; justify-content: center; }
    button[kind="secondaryFormSubmit"] {
        border: 2px solid #2e7d32 !important;
        color: #2e7d32 !important;
        font-weight: bold !important;
    }
</style>
""", unsafe_allow_html=True)

# 3. UBICACIÓN
loc = get_geolocation(component_key="gps_tasacion_final")
texto_ubicacion = "PENDIENTE"
if loc and isinstance(loc, dict) and 'coords' in loc:
    texto_ubicacion = location_manager.codificar_coordenadas(loc['coords']['latitude'], loc['coords']['longitude'])

# 4. CONEXIÓN GOOGLE
if "vertex_client" not in st.session_state:
    try:
        creds = dict(st.secrets["google"])
        st.session_state.vertex_client = ia_engine.conectar_vertex(creds)
    except Exception as e:
        st.error(f"Error credenciales: {e}")

# 5. LOGO
# ... (Partes anteriores de importación y CSS se mantienen igual)

# 5. LOGO (Actualizado a agricolanoroestelogo.jpg)
try:
    st.image("agricolanoroestelogo.jpg", width=300)
except:
    st.warning("⚠️ Logo no encontrado.")

st.title("Tasación Experta K-Factor")

# --- INICIALIZACIÓN DE ESTADO PARA PERSISTENCIA ---
if "marca" not in st.session_state: st.session_state.marca = "John Deere"
if "modelo" not in st.session_state: st.session_state.modelo = ""
if "anio" not in st.session_state: st.session_state.anio = ""
if "horas" not in st.session_state: st.session_state.horas = ""
if "obs" not in st.session_state: st.session_state.obs = ""
if "fotos_cargadas" not in st.session_state: st.session_state.fotos_cargadas = []

# 6. FORMULARIO (Se muestra si NO hay informe generado)
if "informe_final" not in st.session_state:
    with st.form("form_tasacion"):
        st.caption("📸 **Fotos del tractor**")
        fotos = st.file_uploader("Imágenes", accept_multiple_files=True, type=['jpg','png'], key="uploader")
        
        # Lógica de persistencia de fotos
        fotos_a_procesar = fotos if fotos else st.session_state.fotos_cargadas
        if not fotos and st.session_state.fotos_cargadas:
            st.info(f"✅ Manteniendo {len(st.session_state.fotos_cargadas)} fotos anteriores.")

        st.divider()
        
        c1, c2 = st.columns(2)
        with c1:
            marca = st.text_input("Marca", value=st.session_state.marca)
            modelo = st.text_input("Modelo", value=st.session_state.modelo)
        with c2:
            anio = st.text_input("Año", value=st.session_state.anio)
            horas = st.text_input("Horas", value=st.session_state.horas)
        
        obs = st.text_area("Observaciones (Estado, Neumáticos, Garantía...)", value=st.session_state.obs)
        
        submit = st.form_submit_button("🚀 CALCULAR TASACIÓN K-FACTOR", use_container_width=True)

    if submit:
        if marca and modelo and fotos_a_procesar:
            # Guardamos todo en el estado antes de procesar
            st.session_state.update({
                "marca": marca, "modelo": modelo, "anio": anio, 
                "horas": horas, "obs": obs, "fotos_cargadas": fotos_a_procesar
            })

            with st.spinner("Buscando modelo y aplicando algoritmo 10/8/9..."):
                try:
                    # Llamada a la IA (ella buscará los CV y aplicará el K-Factor)
                    inf = ia_engine.realizar_peritaje(
                        st.session_state.vertex_client,
                        marca, modelo, anio, horas, obs, fotos_a_procesar
                    )
                    
                    st.session_state.informe_final = inf
                    st.session_state.fotos_pil = [Image.open(f) for f in fotos_a_procesar]
                    
                    # Generar HTML para descarga y Drive
                    html_final = html_generator.generar_informe_html(
                        marca, modelo, inf, st.session_state.fotos_pil, texto_ubicacion
                    )
                    st.session_state.html = html_final
                    
                    # Backup en Drive
                    try:
                        creds = dict(st.secrets["google"])
                        google_drive_manager.subir_informe(creds, f"Tasacion_{marca}_{modelo}.html", html_final)
                    except: pass
                    
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.warning("⚠️ Faltan datos obligatorios o fotos.")

# 7. PANTALLA DE RESULTADOS
else:
    st.markdown(st.session_state.informe_final)
    st.divider()
    
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        st.download_button("📥 DESCARGAR INFORME", data=st.session_state.html, 
                           file_name=f"Tasacion_{st.session_state.marca}.html", mime="text/html", use_container_width=True)
    
    with col_btn2:
        # AQUÍ ESTÁ EL BOTÓN RECUPERADO
        if st.button("🔄 AJUSTAR Y RE-TASAR", use_container_width=True):
            # Borramos el informe para que el flujo vuelva al formulario, 
            # pero los datos (marca, modelo, fotos...) siguen en st.session_state
            del st.session_state.informe_final
            st.rerun()
    
    if st.button("🆕 NUEVA TASACIÓN (LIMPIAR TODO)", use_container_width=False):
        st.session_state.clear()
        st.rerun()
