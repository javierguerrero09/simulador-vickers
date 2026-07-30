import os
import requests
import streamlit as st

# 1. Traer de forma oculta el token desde las variables del servidor
GITHUB_TOKEN = os.environ.get("MY_GITHUB_TOKEN")

# 2. Configurar la ruta de tu archivo privado
# Reemplazá 'TU_USUARIO' y 'TU_REPO_PRIVADO' con tus datos reales de GitHub
USER = "javierguerrero09"
REPO = "simulador-vickers-privado"
FILE_PATH = "vickers_sim.py"
BRANCH = "main" # o 'master', según cómo se llame tu rama principal

url = f"https://raw.githubusercontent.com/{USER}/{REPO}/{BRANCH}/{FILE_PATH}"

# 3. Autenticarse contra GitHub de manera invisible para el cliente
headers = {"Authorization": f"token {GITHUB_TOKEN}"}

try:
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        # Se descarga el código en la memoria RAM del servidor y se ejecuta
        codigo_fuente = response.text
        exec(codigo_fuente)
    else:
        st.error("Error de autenticación: No se pudo conectar con el servidor central.")

except Exception as e:
    st.error("Error crítico al inicializar el software. Contacte al soporte.")