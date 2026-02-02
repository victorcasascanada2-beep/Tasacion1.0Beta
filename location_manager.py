import base64
import requests

def _encode(texto):
    """Codifica texto a Base64."""
    return base64.b64encode(texto.encode()).decode()

def _obtener_nombre_pueblo(lat, lon):
    """Intenta sacar el nombre del pueblo con las coordenadas."""
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json&zoom=14"
        # User-Agent es obligatorio para que no nos bloqueen
        res = requests.get(url, headers={'User-Agent': 'tasador-app-v1'}, timeout=2)
        if res.status_code == 200:
            data = res.json()
            addr = data.get('address', {})
            return addr.get('village') or addr.get('town') or addr.get('city') or "Zona Rural"
    except:
        pass
    return None

def obtener_ubicacion_final(coords):
    """
    Función principal llamada desde app.py.
    Recibe: coords -> Tupla (lat, lon) o None.
    Devuelve: Texto codificado (LOC_...)
    """
    # 1. Si la App nos pasa coordenadas GPS válidas
    if coords and isinstance(coords, tuple):
        lat, lon = coords
        pueblo = _obtener_nombre_pueblo(lat, lon)
        if pueblo:
            return f"LOC_{_encode(pueblo)}"
        else:
            # Tenemos coordenadas pero no pueblo -> Devolvemos coords cifradas
            raw = f"{lat},{lon}"
            return f"LOC_GPS_{_encode(raw)}"

    # 2. Si coords es None (el GPS falló o está cargando), usamos la IP como respaldo
    try:
        res = requests.get('https://ipapi.co/json/', timeout=2)
        if res.status_code == 200:
            data = res.json()
            ciudad = data.get('city', 'España')
            return f"LOC_NET_{_encode(ciudad)}"
    except:
        pass

    # 3. Si todo falla
    return f"LOC_{_encode('Desconocido')}"
