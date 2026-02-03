import base64

def codificar_coordenadas(lat, lon):
    """
    Recibe latitud y longitud puras (números).
    Devuelve el código cifrado para el informe (LOC_GPS_...).
    NO conecta a internet. NO busca pueblos. SOLO formatea.
    """
    if lat is None or lon is None:
        return "LOC_PENDIENTE"
        
    # Creamos el string simple: "41.503,-5.75"
    datos_raw = f"{lat},{lon}"
    
    # Lo codificamos en Base64 para el informe
    # Resultado ejemplo: "LOC_GPS_NDEuNTIsLTUuNzU="
    b64 = base64.b64encode(datos_raw.encode()).decode()
    
    return f"LOC_GPS_{b64}"
