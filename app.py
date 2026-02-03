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
        padding-bottom: 2rem !important;
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

# 5. LOGO (Actualizado a agricolanoroestelogo.jpg)
try:
    st.image("agricolanoroestelogo.jpg", width=300)
except:
    st.warning("⚠️ Logo no encontrado.")

st.title("Tasación Experta")

# --- INICIALIZACIÓN DE ESTADO PARA PERSISTENCIA ---
if "marca" not in st.session_state: st.session_state.marca = "John Deere"
if "modelo" not in st.session_state: st.session_state.modelo = ""
if "anio" not in st.session_state: st.session_state.anio = ""
if "horas" not in st.session_state: st.session_state.horas = ""
if "obs" not in st.session_state: st.session_state.obs = ""

# 6. FORMULARIO (Siempre visible si no hay informe o si se quiere editar)
if "informe_final" not in st.session_state:
    with st.form("form_tasacion"):
        st.caption("📸 **Sube las fotos ahora**")
        fotos = st.file_uploader("Imágenes del vehículo", accept_multiple_files=True, type=['jpg','png'])
        
        st.divider()
        
        c1, c2 = st.columns(2)
        with c1:
            marca = st.text_input("Marca", value=st.session_state.marca)
            modelo = st.text_input("Modelo", value=st.session_state.modelo, placeholder="Ej: 6155R")
        with c2:
            anio = st.text_input("Año", value=st.session_state.anio, placeholder="Ej: 2018")
            horas = st.text_input("Horas", value=st.session_state.horas, placeholder="Ej: 5000")
        
        obs = st.text_area("Observaciones / Extras", value=st.session_state.obs, placeholder="Ej: Ruedas al 80%...")
        
        submit = st.form_submit_button("🚀 TASAR AHORA", use_container_width=True)

    if submit:
        if marca and modelo and fotos:
            # Guardamos en session_state para que no se pierdan al re-tasar
            st.session_state.marca = marca
            st.session_state.modelo = modelo
            st.session_state.anio = anio
            st.session_state.horas = horas
            st.session_state.obs = obs

            with st.spinner("Analizando y consultando mercado..."):
                notas_ia = f"{obs}\n\n[ID_VERIFICACIÓN: {texto_ubicacion}]"
                try:
                    inf = ia_engine.realizar_peritaje(
                        st.session_state.vertex_client,
                        marca, modelo, int(anio), int(horas),
                        notas_ia, fotos
                    )
                    
                    st.session_state.informe_final = inf
                    st.session_state.fotos_final = [Image.open(f) for f in fotos]
                    
                    html_final = html_generator.generar_informe_html(
                        marca, modelo, inf, st.session_state.fotos_final, texto_ubicacion
                    )
                    st.session_state.html = html_final
                    
                    # Subida a Drive
                    try:
                        creds = dict(st.secrets["google"])
                        google_drive_manager.subir_informe(creds, f"Tasacion_{marca}_{modelo}.html", html_final)
                        st.session_state.drive_status = "✅ Copia de seguridad en Drive"
                    except:
                        st.session_state.drive_status = "⚠️ No se pudo subir a Drive"
                    
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.warning("⚠️ Faltan datos o fotos.")

# 7. RESULTADOS
else:
    if "drive_status" in st.session_state:
        st.caption(st.session_state.drive_status)

    st.markdown(st.session_state.informe_final)
    st.divider()
    
    c1, c2 = st.columns(2)
    with c1:
        st.download_button("📥 DESCARGAR HTML", data=st.session_state.html, 
                           file_name=f"Tasacion_{st.session_state.marca}.html", mime="text/html", use_container_width=True)
    with c2:
        if st.button("🔄 AJUSTAR Y RE-TASAR", use_container_width=True):
            # Borramos solo el informe para que el formulario vuelva a aparecer con los datos guardados
            del st.session_state.informe_final
            if "drive_status" in st.session_state: del st.session_state.drive_status
            st.rerun()
    
    if st.button("🆕 NUEVA TASACIÓN (LIMPIAR TODO)", use_container_width=False):
        st.session_state.clear()
        st.rerun()
