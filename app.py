import os
import requests
import streamlit as st

GITHUB_TOKEN = os.environ.get("MY_GITHUB_TOKEN")

USER = "javierguerrero09"
REPO = "simulador-vickers-privado"
FILE_PATH = "vickers_sim.py"
BRANCH = "main"

url = f"https://raw.githubusercontent.com/{USER}/{REPO}/{BRANCH}/{FILE_PATH}"

headers = {"Authorization": f"token {GITHUB_TOKEN}"}

try:
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        codigo_fuente = response.text
        exec(codigo_fuente)
    else:
        st.error("Error de autenticación: No se pudo conectar con el servidor central.")

except Exception as e:
    st.error("Error crítico al inicializar el software. Contacte al soporte.")
