import streamlit as st
from streamlit_js_eval import get_geolocation
import base64
import requests
import time

def _obtener_nombre_pueblo(lat, lon):
    """Traduce coordenadas a nombre de pueblo (como ayer en Malva)."""
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json&zoom=14"
        res = requests.get(url, headers={'User-Agent': 'tasador-agricola'}, timeout=3)
        data = res.json()
        addr = data.get('address', {})
        return addr.get('village') or addr.get('town') or addr.get('city') or "Zamora"
    except:
        return "Castilla y Leon"

def obtener_ubicacion():
    """Motor híbrido: GPS rápido o Red instantánea."""
    # 1. Intento de GPS (espera activa de 3 segundos)
    loc = get_geolocation(component_key="gps_malva_fix")
    
    if loc and isinstance(loc, dict) and 'coords' in loc:
        pueblo = _obtener_nombre_pueblo(loc['coords']['latitude'], loc['coords']['longitude'])
        b64 = base64.b64encode(pueblo.encode()).decode()
        return f"LOC_{b64}"

    # 2. Si el GPS no responde (como en el portátil), usamos la RED
    try:
        res = requests.get('https://ipapi.co/json/', timeout=2)
        if res.status_code == 200:
            data = res.json()
            pueblo = data.get('city', 'Zamora')
            b64 = base64.b64encode(pueblo.encode()).decode()
            return f"LOC_NET_{b64}"
    except:
        pass

    return "LOC_BUSCANDO"
