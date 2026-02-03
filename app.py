import streamlit as st
from PIL import Image
from streamlit_js_eval import get_geolocation # La clave del éxito de "Dondeestoy"
import ia_engine
import html_generator
import google_drive_manager
import location_manager # Nuestro nuevo formateador simple

# -------------------------------------------------
# 1. CONFIGURACIÓN
# -------------------------------------------------
st.set_page_config(page_title="Tasador Agrícola", page_icon="🚜", layout="centered")

# CSS Limpio
st.markdown("""
<style>
    [data-testid="stToolbar"], footer {display: none;}
    .block-container { padding-top: 3rem !important; }
    [data-testid="stImage"] { display: flex; justify-content: center; }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# 2. LÓGICA DE UBICACIÓN (ARQUITECTURA "DONDEESTOY")
# -------------------------------------------------
# Llamada directa, sin lógica compleja intermedia
loc = get_geolocation(component_key="gps_tasacion_final")

# Variable por defecto
texto_ubicacion = "LOC_PENDIENTE"

if loc:
    if 'coords' in loc:
        lat = loc['coords']['latitude']
        lon = loc['coords']['longitude']
        
        # Aquí usamos el manager SOLO para formatear el texto, no para buscar nada
        texto_ubicacion = location_manager.codificar_coordenadas(lat, lon)
        
        # Feedback visual discreto (opcional, para que sepas que funciona)
        # st.success(f"GPS Activo: {lat}, {lon}") 
    elif 'error' in loc:
        st.warning("⚠️ Permiso de ubicación denegado. Se usará modo genérico.")

# -------------------------------------------------
# 3. CONEXIÓN GOOGLE (VERTEX)
# -------------------------------------------------
if "vertex_client" not in st.session_state:
    try:
        creds = dict(st.secrets["google"])
        st.session_state.vertex_client = ia_engine.conectar_vertex(creds)
    except Exception as e:
        st.error(f"Error de credenciales: {e}")

# -------------------------------------------------
# 4. INTERFAZ
# -------------------------------------------------
# Corrección: Solo una vez el nombre de la variable y la URL limpia
logo_url = "https://raw.githubusercontent.com/victorcasascanada2-beep/Tasacion1.0Beta/main/afoto.png"

st.image(logo_url, width=300)
st.title("Tasación Experta")
st.caption("Sistema de valoración profesional")

if "informe_final" not in st.session_state:
    with st.form("form_tasacion"):
        col1, col2 = st.columns(2)
        with col1:
            marca = st.text_input("Marca", placeholder="John Deere")
            modelo = st.text_input("Modelo", placeholder="6155R")
        with col2:
            anio_txt = st.text_input("Año", value="2018")
            horas_txt = st.text_input("Horas", value="5000")
        
        observaciones = st.text_area("Notas / Extras")
        fotos = st.file_uploader("Fotos", accept_multiple_files=True, type=['jpg', 'png'])
        
        submit = st.form_submit_button("🚀 TASAR AHORA", use_container_width=True)

    if submit:
        if not (marca and modelo and fotos):
            st.warning("Faltan datos obligatorios.")
        else:
            with st.spinner("Procesando tasación..."):
                try:
                    # Pasamos la ubicación ya formateada a la IA
                    notas_ia = f"{observaciones}\n\n[UBICACION_COORDS: {texto_ubicacion}]"
                    
                    inf = ia_engine.realizar_peritaje(
                        st.session_state.vertex_client, 
                        marca, modelo, int(anio_txt), int(horas_txt), 
                        notas_ia, fotos
                    )
                    
                    # Guardamos sesión
                    st.session_state.informe_final = inf
                    st.session_state.fotos_final = [Image.open(f) for f in fotos]
                    st.session_state.marca_final = marca
                    st.session_state.modelo_final = modelo
                    
                    # Generamos HTML
                    st.session_state.html_listo = html_generator.generar_informe_html(
                        marca, modelo, inf, st.session_state.fotos_final, texto_ubicacion
                    )
                    
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

# -------------------------------------------------
# 5. RESULTADOS
# -------------------------------------------------
if "informe_final" in st.session_state:
    st.markdown(st.session_state.informe_final)
    
    # Botones de descarga y Drive...
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.download_button("📥 DESCARGAR", data=st.session_state.html_listo, file_name="tasacion.html", mime="text/html")
    
    with c2:
        if st.button("☁️ DRIVE"):
            creds = dict(st.secrets["google"])
            nombre = f"Tasacion_{st.session_state.marca_final}.html"
            google_drive_manager.subir_informe(creds, nombre, st.session_state.html_listo)
            st.success("Subido")
            
    with c3:
        if st.button("🔄 NUEVA"):
            st.session_state.clear()
            st.rerun()
