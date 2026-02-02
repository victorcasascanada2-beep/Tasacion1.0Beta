import io
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2 import service_account

ID_CARPETA_DRIVE = "0AEU0RHjR-mDOUk9PVA" 
SCOPES = ["https://www.googleapis.com/auth/drive"]

def subir_informe(creds_dict, nombre_archivo, contenido_html):
    try:
        creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        service = build('drive', 'v3', credentials=creds)

        # --- CORRECCIÓN DEFINITIVA ---
        # Si el contenido ya son bytes, lo usamos tal cual. 
        # Si es texto (string), lo convertimos a bytes.
        if isinstance(contenido_html, str):
            datos_a_subir = contenido_html.encode('utf-8')
        else:
            datos_a_subir = contenido_html 

        file_metadata = {
            'name': nombre_archivo,
            'parents': [ID_CARPETA_DRIVE],
            'mimeType': 'text/html'
        }
        
        fh = io.BytesIO(datos_a_subir)
        media = MediaIoBaseUpload(fh, mimetype='text/html', resumable=True)

        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id',
            supportsAllDrives=True 
        ).execute()

        return file.get('id')

    except Exception as e:
        print(f"Error crítico en Drive: {str(e)}")
        return None
