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

# -------------------------------------------------
# 2. CSS "MODO APP NATIVA" (Sin barras ni huecos)
# -------------------------------------------------
st.markdown("""
<style>
    /* 1. Desaparece todo lo de Streamlit */
    header[data-testid="stHeader"] { display: none !important; }
    [data-testid="stToolbar"] { display: none !important; }
    footer { display: none !important; }
    
    /* 2. CONTENEDOR PRINCIPAL: PEGADO AL TECHO */
    .block-container { 
        margin-top: -3rem !important; /* Absorbe el hueco fantasma */
        padding-top: 1rem !important; /* Espacio de seguridad mínimo */
        padding-bottom: 2rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    
    /* 3. LOGO Y BOTONES */
    [data-testid="stImage"] { display: flex; justify-content: center; }
    
    /* Botón de Tasar más visible */
    button[kind="secondaryFormSubmit"] {
        border: 2px solid #2e7d32 !important;
        color: #2e7d32 !important;
        font-weight: bold !important;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# 3. UBICACIÓN (ARQUITECTURA "DONDEESTOY")
# -------------------------------------------------
loc = get_geolocation(component_key="gps_tasacion_final")
texto_ubicacion = "PENDIENTE"

if loc and isinstance(loc, dict) and 'coords' in loc:
    lat = loc['coords']['latitude']
    lon = loc['coords']['longitude']
    # Formateo simple a Base64
    texto_ubicacion = location_manager.codificar_coordenadas(lat, lon)

# -------------------------------------------------
# 4. CONEXIÓN GOOGLE
# -------------------------------------------------
if "vertex_client" not in st.session_state:
    try:
        creds = dict(st.secrets["google"])
        st.session_state.vertex_client = ia_engine.conectar_vertex(creds)
    except Exception as e:
        st.error(f"Error credenciales: {e}")

# -------------------------------------------------
# 5. INTERFAZ (LOGO BLINDADO)
# -------------------------------------------------
if os.path.exists("afoto.png"):
    st.image("afoto.png", width=300)
else:
    try:
        st.image("https://raw.githubusercontent.com/victorcasascanada2-beep/Tasacion1.0Beta/main/afoto.png", width=300)
    except:
        st.warning("⚠️ Logo no cargado, sistema operativo.")

st.title("Tasación Experta")

# -------------------------------------------------
# 6. FORMULARIO (EL CORAZÓN DE LA APP)
# -------------------------------------------------
if "informe_final" not in st.session_state:
    # AQUI ESTABA EL ERROR: Todo esto debe estar indentado dentro del 'with'
    with st.form("form_tasacion"):
        c1, c2 = st.columns(2)
        with c1:
            marca = st.text_input("Marca", placeholder="Ej: John Deere")
            modelo = st.text_input("Modelo", placeholder="Ej: 6155R")
        with c2:
            anio = st.text_input("Año", value="2018")
            horas = st.text_input("Horas", value="5000")
        
        obs = st.text_area("Observaciones / Extras")
        fotos = st.file_uploader("Fotos del tractor", accept_multiple_files=True, type=['jpg','png'])
        
        # EL BOTÓN DEBE ESTAR DENTRO DEL FORM (Indentado)
        submit = st.form_submit_button("🚀 TASAR AHORA", use_container_width=True)

    # Lógica de procesado (fuera del form, pero reacciona al botón)
    if submit:
        if marca and modelo and fotos:
            with st.spinner("Analizando y guardando en la nube..."):
                # 1. Generamos el ID y texto IA
                notas_ia = f"{obs}\n\n[ID_VERIFICACIÓN: {texto_ubicacion}]"
                
                try:
                    # Llamada a la IA
                    inf = ia_engine.realizar_peritaje(
                        st.session_state.vertex_client,
                        marca, modelo, int(anio), int(horas),
                        notas_ia, fotos
                    )
                    
                    # Guardamos sesión
                    st.session_state.informe_final = inf
                    st.session_state.fotos_final = [Image.open(f) for f in fotos]
                    st.session_state.marca = marca
                    st.session_state.modelo = modelo
                    
                    # Generamos HTML
                    html_final = html_generator.generar_informe_html(
                        marca, modelo, inf, st.session_state.fotos_final, texto_ubicacion
                    )
                    st.session_state.html = html_final
                    
                    # --- SUBIDA AUTOMÁTICA A DRIVE (Invisible) ---
                    try:
                        creds = dict(st.secrets["google"])
                        nombre_archivo = f"Tasacion_{marca}_{modelo}.html"
                        google_drive_manager.subir_informe(creds, nombre_archivo, html_final)
                        st.session_state.drive_status = "✅ Copia de seguridad guardada en Drive"
                    except Exception as e:
                        st.session_state.drive_status = "⚠️ No se pudo subir a Drive (Internet inestable)"
                    # ---------------------------------------------

                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error en el proceso: {e}")
        else:
            st.warning("Por favor, rellena Marca, Modelo y sube al menos una foto.")

# -------------------------------------------------
# 7. RESULTADOS (LIMPIOS)
# -------------------------------------------------
if "informe_final" in st.session_state:
    # Aviso discreto de Drive
    if "drive_status" in st.session_state:
        st.caption(st.session_state.drive_status)

    st.markdown(st.session_state.informe_final)
    st.divider()
    
    # Solo 2 botones: Descargar y Nueva (Drive ya se hizo solo)
    c1, c2 = st.columns(2)
    
    with c1:
        st.download_button(
            "📥 DESCARGAR", 
            data=st.session_state.html, 
            file_name=f"Tasacion_{st.session_state.marca}.html",
            mime="text/html",
            use_container_width=True
        )
            
    with c2:
        if st.button("🔄 NUEVA", use_container_width=True):
            st.session_state.clear()
            st.rerun()
