# config_prompt.py

def obtener_prompt_tasacion(marca, modelo, anio, horas, observaciones):
    return f"""
            Actúa como experto tasador de Agrícola Noroeste. Busca y cerciorate de que los datos son reales
            Analiza este {marca} {modelo} del año {anio} con {horas} horas.
            
            TAREAS:
            1. Analiza el estado visual a través de las fotos adjuntas. No des una salida de comentarios mas alla de 30 palabras por foto
            2. Busca precios reales de mercado en Agriaffaires, Tractorpool y E-farm para unidades similares.
            3. Genera una tabla comparativa de 10-15 unidades.
            4. Calcula:
               - Precio Venta (Aterrizaje).
               - Precio Compra recomendado para Agrícola Noroeste.
            
            Notas adicionales: {observaciones}
            
    """
