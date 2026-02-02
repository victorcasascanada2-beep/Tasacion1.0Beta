import streamlit as st
from google import genai
from google.oauth2 import service_account
from PIL import Image
import io
import config_prompt

def conectar_vertex(creds_dict):
    raw_key = str(creds_dict.get("private_key", ""))
    clean_key = raw_key.strip().strip('"').strip("'").replace("\\n", "\n")
    creds_dict["private_key"] = clean_key
    google_creds = service_account.Credentials.from_service_account_info(
        creds_dict, 
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    return genai.Client(vertexai=True, project=creds_dict.get("project_id"), 
                        location="us-central1", credentials=google_creds)

def realizar_peritaje(client, marca, modelo, anio, horas, observaciones, lista_fotos):
    fotos_ia = []
    
    # --- OPTIMIZACIÓN DE TOKENS ---
    for foto in lista_fotos:
        img = Image.open(foto).convert("RGB")
        
        # 1. Redimensionamos a 800px (Suficiente para ver desgaste y extras)
        # Antes estaba a 1200px o original, que es un desperdicio.
        img.thumbnail((800, 800)) 
        
        buf = io.BytesIO()
        # 2. Compresión JPEG al 75% (Elimina datos invisibles)
        img.save(buf, format="JPEG", quality=75) 
        buf.seek(0)
        
        fotos_ia.append(Image.open(buf))
    # -------------------------------

    prompt = config_prompt.obtener_prompt_tasacion(marca, modelo, anio, horas, observaciones)

    try:
        response = client.models.generate_content(
            model="gemini-2.5-pro", 
            contents=[prompt] + fotos_ia,
            config={
                "tools": [{"google_search": {}}],
                "temperature": 0.35,
                "max_output_tokens": 4096
            }
        )
        return response.text
    except Exception as e:
        return f"Error en el motor: {str(e)}"
