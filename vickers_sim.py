# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------
# PROYECTO: Vickers Precision Multi-Test
# VERSIÓN:  1.0.10
# AUTOR:    Javier Paolantonio Guerrero
# 
# Registrado ante la Dirección Nacional del Derecho de Autor (DNDA)
# Legajo Nº: RL-2026-71651411-APN-DNDA#MJ
# Copyright © 2026 - Todos los derechos reservados
# ----------------------------------------------------------------------
import streamlit as st
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import random
import base64
import os
from io import BytesIO
from math import floor

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="🔬 Vickers Precision Multi-Test ©", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; font-family: 'Courier New', Courier, monospace; }
    h1, h2, h3 { color: #00ff00 !important; }
    .stButton>button { background-color: #222; color: #00ff00; border: 1px solid #00ff00; font-weight: bold; width: 100%;}
    .stButton>button:hover { background-color: #00ff00; color: #000; }
    [data-testid="stMetricValue"] { color: #ffffff !important; font-size: 32px; font-weight: bold; }
    [data-testid="stMetricLabel"] { color: #e0e0e0 !important; font-size: 18px; }
    .stMetric { background-color: #1a1c23; border: 1px solid #333; padding: 15px; border-radius: 5px; }
    .overlay-timer {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background-color: #1a1c23;
        border: 2px solid #00ff00;
        padding: 30px;
        border-radius: 10px;
        z-index: 9999;
        text-align: center;
        box-shadow: 0 0 20px rgba(0, 255, 0, 0.4);
        width: 400px;
    }
    /* Estilos específicos para quitar el borde y poner texto negro en los botones explicativos */
    div[data-testid="stSidebarUserContent"] div.stButton button[disabled], 
    div.stButton button[disabled] {
        color: #000000 !important;
        border: none !important;
        background-color: transparent !important;
        cursor: default !important;
    }
            </style>
    """, unsafe_allow_html=True)

# --- FUNCIONES AUXILIARES ---
def obtener_img_base():
    # Nueva resolución duplicada a 1600 x 1200
    base = np.full((1200, 1600, 3), 140, dtype=np.uint8)
    noise = np.random.randint(0, 30, (1200, 1600, 3), dtype=np.uint8)
    return Image.fromarray(base + noise).filter(ImageFilter.GaussianBlur(radius=1))

def img_to_b64(img):
    if img is None: return ""
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

if 'etapa' not in st.session_state:
    st.session_state.etapa = 'ensayo'
    st.session_state.img_original = obtener_img_base()
    st.session_state.historial = []
    # Posición inicial centrada adaptada a 1600 x 1200
    st.session_state.temp_pos = (800, 600)
    st.session_state.l1 = 350.0
    st.session_state.l2 = 450.0
    pool = [True, False, False, False, False]
    random.shuffle(pool)
    while pool[-1] == True:
        random.shuffle(pool)
    st.session_state.pool_defectos = pool
    st.session_state.dureza_base = random.uniform(100, 300)

def renderizar_escena(dibujar_reglillas=False, eje="H"):
    img = st.session_state.img_original.copy()
    draw = ImageDraw.Draw(img)
    # Nueva relación duplicada: 1600px / 280um = 5.71428
    px_scale = 1600 / 280
    for idx, h in enumerate(st.session_state.historial):
        # Dibujamos el cuerpo del rombo
        puntos = h['puntos_fijos']
        draw.polygon(puntos, fill=(60, 60, 60), outline=None)
        
        # --- DIAGONALES CON DEGRADADO DE ESPESOR (EFECTO PIRÁMIDE) ---
        cx, cy = h['pos']
        color_diag = (70, 70, 70)
        ancho_centro = 1.2 # Grosor máximo en el centro

        # Encontramos los puntos más extremos para que las diagonales siempre lleguen al final
        # sin importar si el vértice está redondeado (tiene 2 puntos) o es simple.
        # Función para obtener el punto medio de los extremos (útil para redondeos)
        def obtener_extremo(pts, eje, modo):
            # Encontramos el valor extremo (min o max) en el eje X (0) o Y (1)
            val_extremo = modo([p[eje] for p in pts])
            # Filtramos todos los puntos que comparten ese valor extremo
            coincidentes = [p for p in pts if p[eje] == val_extremo]
            # Si hay varios (redondeo), devolvemos el promedio
            if len(coincidentes) > 1:
                mx = sum(p[0] for p in coincidentes) / len(coincidentes)
                my = sum(p[1] for p in coincidentes) / len(coincidentes)
                return (mx, my)
            return coincidentes[0]

        v_sup_real = obtener_extremo(puntos, 1, min)
        v_inf_real = obtener_extremo(puntos, 1, max)
        v_izq_real = obtener_extremo(puntos, 0, min)
        v_der_real = obtener_extremo(puntos, 0, max)

        # Dibujo de Diagonales
        draw.polygon([v_sup_real, (cx - ancho_centro, cy), (cx + ancho_centro, cy)], fill=color_diag)
        draw.polygon([v_inf_real, (cx - ancho_centro, cy), (cx + ancho_centro, cy)], fill=color_diag)
        draw.polygon([v_izq_real, (cx, cy - ancho_centro), (cx, cy + ancho_centro)], fill=color_diag)
        draw.polygon([v_der_real, (cx, cy - ancho_centro), (cx, cy + ancho_centro)], fill=color_diag)
        # -----------------------------------------------
        # --- PUNTO CENTRAL AJUSTABLE ---
        centro_x, centro_y = h['pos']
        # Radio aumentado proporcionalmente a la nueva resolución
        r_punto = 6
        draw.ellipse([centro_x - r_punto, centro_y - r_punto, 
                      centro_x + r_punto, centro_y + r_punto], 
                     fill=(80, 80, 80))
        ix, iy = h['pos']
        dr = (h['d_real'] * px_scale) / 2
        
        # Intentamos cargar una fuente estándar del sistema con un tamaño escalado de 24px
        try:
            from PIL import ImageFont
            # Intentamos con una fuente común en Windows/Linux/Mac
            fuente_id = ImageFont.truetype("arial.ttf", 24)
        except:
            try:
                fuente_id = ImageFont.load_default(size=24) # Requiere PIL moderno
            except:
                fuente_id = ImageFont.load_default() # Caída segura por compatibilidad
                
        # Separación del texto aumentada y vinculación de la fuente escalada
        draw.text((int(ix+dr+12), int(iy+dr+12)), f"ID: {idx+1}", fill=(0, 255, 0), font=fuente_id)

    if dibujar_reglillas:
        # Mantenemos los valores de l1 y l2 para el cálculo, pero creamos posiciones de dibujo
        color_reg = (0, 255, 0)
        # Sumar 0.5 a una coordenada entera con width impar elimina el anti-aliasing en PIL
        p1 = floor(st.session_state.l1) + 0.5
        p2 = floor(st.session_state.l2) + 0.5
        
        # --- GROSOR DE REGLILLA ADAPTATIVO OPTIMIZADO ---
        z_ref = st.session_state.get('z_actual', 200.0)
        # Escalamos multiplicando con redondeo hacia arriba para compensar la compresión en pantalla
        from math import ceil
        ancho_linea_adaptativo = max(6, int(ceil(6 * (z_ref / 200.0))))
        
        if eje == "H":
            draw.line([(p1, 0), (p1, 1200)], fill=color_reg, width=ancho_linea_adaptativo)
            draw.line([(p2, 0), (p2, 1200)], fill=color_reg, width=ancho_linea_adaptativo)
        else:
            draw.line([(0, p1), (1600, p1)], fill=color_reg, width=ancho_linea_adaptativo)
            draw.line([(0, p2), (1600, p2)], fill=color_reg, width=ancho_linea_adaptativo)
    return img

def obtener_zoom(img_completa, h_idx=-1):
    if not st.session_state.historial: return None
    h_act = st.session_state.historial[h_idx]
    ix, iy = h_act['pos']
    
    # --- LÓGICA ADAPTATIVA EXCLUSIVA PARA HUELLAS GRANDES ---
    px_scale = 1600 / 280
    diametro_px = h_act['d_real'] * px_scale
    
    # Si la huella es igual o mayor al ancho estándar de la ventana de la lupa (400 px debido al cambio de resolución)
    if diametro_px >= 400.0:
        # La ventana completa (2 * z) debe ser 1.25 veces el diámetro de la huella
        z = (1.25 * diametro_px) / 2
    else:
        # En cualquier otro caso, se mantiene el radio estático original duplicado
        z = 200.0
        
    # Guardamos el radio actual en sesión para adaptar el grosor de las líneas en renderizar_escena
    st.session_state['z_actual'] = z
    
    # Calculamos los bordes teóricos
    left = ix - z
    top = iy - z
    right = ix + z
    bottom = iy + z
    
    # Ajustamos si se sale de los bordes para mantener el tamaño 2z x 2z (400x400) adaptado a 1600x1200
    if left < 0:
        right -= left
        left = 0
    if right > 1600:
        left -= (right - 1600)
        right = 1600
    if top < 0:
        bottom -= top
        top = 0
    if bottom > 1200:
        top -= (bottom - 1200)
        bottom = 1200
        
    crop_box = (int(left), int(top), int(right), int(bottom))
    # Ahora el recorte siempre es de 400x400, evitando deformaciones al reescalar a 450x450
    return img_completa.crop(crop_box).resize((450, 450), resample=Image.NEAREST)

def generar_html_reporte(img_distribucion):
    img_dist_b64 = img_to_b64(img_distribucion)
    html = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; padding: 20px; color: #333; }}
            .header {{ text-align: center; border-bottom: 2px solid #333; padding-bottom: 10px; }}
            .distribucion {{ text-align: center; margin: 20px 0; border: 1px solid #ccc; padding: 15px; background: #fff; }}
            /* Ajuste para la vista general en relación 4:3 corregida */
            .distribucion img {{ max-width: 800px; width: 100%; height: auto; border: 1px solid #000; }}
            .item {{ border: 1px solid #ccc; padding: 15px; margin-bottom: 20px; page-break-inside: avoid; }}
            .grid {{ display: flex; gap: 20px; }}
            .data {{ flex: 1; }}
            .images {{ flex: 2; display: flex; gap: 10px; }}
            /* Se especifica la clase exacta para las imágenes de las lupas de auditoría (1:1) */
            .images img {{ border: 1px solid #000; width: 250px; height: 250px; object-fit: contain; }}
            h2 {{ color: #2c3e50; }}
            .label {{ font-weight: bold; }}
        </style>
    </head>
        <body>
        <div class="header">
            <h1>REPORTE TÉCNICO DE COMPETENCIA - VICKERS</h1>
            <p style="font-size: 11px; color: #777; margin-top: -10px; font-family: Arial, sans-serif;">
                            Vickers Precision Multi-Test v1.0.10 | Copyright © 2026 Javier Paolantonio Guerrero | DNDA Reg. Nº: RL-2026-71651411-APN-DNDA#MJ
            </p>
        </div>
        <div class="distribucion">
            <h2>VISTA GENERAL DE DISTRIBUCIÓN (PROBETA)</h2>
            <img src="data:image/png;base64,{img_dist_b64}">
        </div>
    """
    for i, h in enumerate(st.session_state.historial):
        accion = "Descartada" if h['descartada'] else "Medida"
        estado_txt = "Defectuosa" if h['defectuosa'] else "No defectuosa"
        med_txt = "n/a" if h['descartada'] else f"H: {h['m_h']:.1f} / V: {h['m_v']:.1f}"
        
        html += f"""
        <div class="item">
            <h2>Indentación ID: {i+1}</h2>
            <div class="grid">
                <div class="data">
                    <p><span class="label">Carga:</span> {h['carga']} gf</p>
                    <p><span class="label">Tiempo:</span> {h['tiempo']} s</p>
                    <p><span class="label">Operador:</span> {accion}</p>
                    <p><span class="label">Estado:</span> {estado_txt}</p>
                    <p><span class="label">Medición [µm]:</span> {med_txt}</p>
                </div>
                <div class="images">
        """
        if h['descartada']:
            if h['cap_def']: html += f'<img src="data:image/png;base64,{img_to_b64(h["cap_def"])}">'
        else:
            if h['cap_d1']: html += f'<img src="data:image/png;base64,{img_to_b64(h["cap_d1"])}">'
            if h['cap_d2']: html += f'<img src="data:image/png;base64,{img_to_b64(h["cap_d2"])}">'
        
        html += """
                </div>
            </div>
        </div>
        """
    
    # Acá termina el bucle for. El siguiente código va FUERA del bucle:
    html += "</body></html>"
    return html

# --- FLUJO ---
st.markdown("<h1 style='text-align: center;'>🔬 VICKERS PRECISION MULTI-TEST <span style='font-size: 20px; font-weight: normal; '>v1.0.10</span></h1>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

if st.session_state.etapa == 'ensayo':
    st.subheader(f"PREPARAR INDENTACIÓN Nº {len(st.session_state.historial) + 1}")
    c1, c2 = st.columns(2)
    with c1:
        lista_cargas = [0, 5, 10, 25, 50, 100, 200, 300, 400]
        carga = st.selectbox("Carga (gf)", options=lista_cargas, index=0)
        tiempo = st.number_input("Tiempo de permanencia (s)", min_value=0, max_value=60, value=0, step=1)
        
        if len(st.session_state.historial) == 0:
            archivo = st.file_uploader("Subir imagen base", type=["jpg", "png"])
            if archivo: st.session_state.img_original = Image.open(archivo).resize((1600, 1200))
        
        curr_x, curr_y = st.session_state.temp_pos
        # Vinculación directa con session_state usando 'key' adaptada a 1600 x 1200
        cx = st.slider("Posición X", 0, 1600, value=int(st.session_state.temp_pos[0]), key="slider_x")
        cy = st.slider("Posición Y", 0, 1200, value=int(st.session_state.temp_pos[1]), key="slider_y")
        
        # Actualizamos temp_pos inmediatamente
        st.session_state.temp_pos = (cx, cy)
        
        if st.button("EJECUTAR ENSAYO"):
            if carga == 0 or tiempo == 0:
                st.error("⚠️ DEBE SELECCIONAR CARGA Y TIEMPO SUPERIOR A 0.")
            else:
                ## --- CUADRO FLOTANTE SUPERPUESTO (VELOCIDAD INTERMEDIA AJUSTADA A 0.9S) ---
                import time
                overlay = st.empty()
                for i in range(tiempo + 1):
                    with overlay.container():
                        porcentaje = i / tiempo
                        segundos_restantes = tiempo - i
                        st.markdown(f"""
                            <div class="overlay-timer">
                                <h2 style="margin: 0; color: #00ff00;">🔬 Aplicando Carga...</h2>
                                <p style="color: white; font-size: 18px;">Tiempo de permanencia: {tiempo}s</p>
                                <div style="background-color: #333; border-radius: 5px; height: 20px; width: 100%;">
                                    <div style="background-color: #00ff00; height: 100%; width: {porcentaje*100}%; border-radius: 5px; transition: width 0.38s;"></div>
                                </div>
                                <p style="margin-top: 15px; color: #00ff00; font-weight: bold;">FALTAN: {segundos_restantes}s</p>
                            </div>
                        """, unsafe_allow_html=True)
                    if i < tiempo:
                        time.sleep(0.75) # Ajustado exactamente a 0.75s para un comportamiento casi real pero optimizado
                overlay.empty() # Elimina el cuadro al finalizar
                # ------------------------------------
                # Oscilación real del material (Brecha de 50 HV en total: +/- 25 HV respecto a la base)
                variacion_fija = 25.0
                hv = random.uniform(st.session_state.dureza_base - variacion_fija, 
                                    st.session_state.dureza_base + variacion_fija)
                d_real = np.sqrt(1.8544 * (carga/1000) / hv) * 1000
                # Ajuste de tamaño por tiempo de permanencia
                if 1 <= tiempo <= 9:
                    # Empieza en 0.40 (1s) y suma 0.05 por cada segundo adicional
                    factor_tiempo = 0.40 + (tiempo - 1) * 0.05
                elif tiempo >= 10:
                    factor_tiempo = 1.0
                else:
                    factor_tiempo = 1.0 # Caso por defecto para evitar errores
                
                d_real = d_real * factor_tiempo
                
                # Reiniciamos el zoom al valor base para evitar el efecto memoria de ensayos anteriores
                st.session_state['z_actual'] = 100.0
                
                # NUEVA LÓGICA DE BLOQUE: Evita defecto en el primer ensayo del bloque
                if not st.session_state.pool_defectos:
                    nuevo_pool = [True, False, False, False, False]
                    random.shuffle(nuevo_pool)
                    while nuevo_pool[-1] == True:  # El último en salir del pool (pop) es el primero del bloque
                        random.shuffle(nuevo_pool)
                    st.session_state.pool_defectos = nuevo_pool
                
                defect = st.session_state.pool_defectos.pop()

                # --- NUEVA LÓGICA DE ASIMETRÍA MÁXIMA DEL 4% EN LA DIAGONAL VERTICAL ---
                # La diagonal horizontal mantiene su valor original nominal (f_h = 1.0)
                f_h = 1.0
                # La diagonal vertical varía aleatoria en un rango de +/- 4% respecto a la horizontal
                f_v = random.uniform(0.960, 1.040)
                px_scale = 1600 / 280
                dr_h, dr_v = (d_real * px_scale * f_h) / 2, (d_real * px_scale * f_v) / 2
                ix, iy = cx, cy

                # Vértices base
                v_sup = (ix, iy - dr_v)
                v_der = (ix + dr_h, iy)
                v_inf = (ix, iy + dr_v)
                v_izq = (ix - dr_h, iy)

                tipo_def = random.choice(['redondeado', 'asimetrico', 'arrastre']) if defect else 'ninguno'
                
                # --- LÓGICA DE DEFECTOS POR PORCENTAJES ---
                # Definimos un factor de desvío del 5% del radio de la diagonal
                desvio_pct = dr_h * 0.05 

                if tipo_def == 'redondeado':
                    idx = random.randint(0, 3)
                    puntos = [v_sup, v_der, v_inf, v_izq]
                    px, py = puntos[idx]
                    
                    # Aumentamos el ancho del plano al 15% del radio
                    ancho_plano = dr_h * 0.15 
                    # Hundimos el plano un 4% hacia el centro para que sea indiscutible el defecto
                    sangria = dr_h * 0.04 

                    if idx == 0: # Vértice Superior
                        puntos[0:1] = [(px - ancho_plano/2, py + sangria), (px + ancho_plano/2, py + sangria)]
                    elif idx == 1: # Vértice Derecho
                        puntos[1:2] = [(px - sangria, py - ancho_plano/2), (px - sangria, py + ancho_plano/2)]
                    elif idx == 2: # Vértice Inferior
                        puntos[2:3] = [(px + ancho_plano/2, py - sangria), (px - ancho_plano/2, py - sangria)]
                    else: # Vértice Izquierdo
                        puntos[3:4] = [(px + sangria, py + ancho_plano/2), (px + sangria, py - ancho_plano/2)]

                elif tipo_def == 'asimetrico':
                    # Desplazamiento agresivo del 30% en dos vértices para romper la simetría
                    desvio_asimetrico = dr_h * 0.30
                    # Estiramiento adicional del 15%
                    estiramiento_asimetrico = dr_h * 0.15
                    
                    # Decisión aleatoria de cuál vértice se estira: 'superior' o 'derecho'
                    vertice_a_estirar = random.choice(['superior', 'derecho'])
                    
                    if vertice_a_estirar == 'superior':
                        # Se desplaza y se estira el superior (restando en Y), el derecho solo se desplaza
                        v_sup_mod = (ix + desvio_asimetrico, iy - dr_v - estiramiento_asimetrico)
                        v_der_mod = (ix + dr_h, iy + desvio_asimetrico)
                    else:
                        # El superior solo se desplaza, se desplaza y se estira el derecho (sumando en X)
                        v_sup_mod = (ix + desvio_asimetrico, iy - dr_v)
                        v_der_mod = (ix + dr_h + estiramiento_asimetrico, iy + desvio_asimetrico)
                        
                    puntos = [v_sup_mod, v_der_mod, v_inf, v_izq]

                elif tipo_def == 'arrastre':
                    idx = random.randint(0, 3)
                    puntos = [v_sup, v_der, v_inf, v_izq]
                    px, py = puntos[idx]
                    # Estira el vértice un 25% del radio hacia afuera
                    estiramiento = dr_h * 0.25
                    if idx == 0: puntos[0] = (px, py - estiramiento)
                    elif idx == 1: puntos[1] = (px + estiramiento, py)
                    elif idx == 2: puntos[2] = (px, py + estiramiento)
                    else: puntos[3] = (px - estiramiento, py)
                else:
                    puntos = [v_sup, v_der, v_inf, v_izq]
                # --------------------------------
                
                st.session_state.historial.append({
                    'pos':(cx,cy), 'd_real':d_real, 'defectuosa':defect, 'puntos_fijos': puntos, 
                    'carga': carga, 'tiempo': tiempo, 'descartada': False, 'cap_d1': None, 'cap_d2': None, 
                    'cap_def': None, 'm_h': 0.0, 'm_v': 0.0
                })
                # Distancia inicial duplicada a 90 píxeles para corresponder al nuevo px_scale
                st.session_state.l1, st.session_state.l2 = float(cx-90), float(cx+90)
                st.session_state.etapa = 'medir_d1'; st.rerun()

        # Botón removido de la columna 1 para posicionarse abajo del divisor continuo
        pass

    with c2:
        img_p = renderizar_escena()
        p_draw = ImageDraw.Draw(img_p)
        # Retícula roja escalada a la nueva resolución (longitud 50 y grosor 4)
        p_draw.line([(cx-50, cy), (cx+50, cy)], fill=(255, 0, 0), width=4)
        p_draw.line([(cx, cy-50), (cx, cy+50)], fill=(255, 0, 0), width=4)
        st.image(img_p, caption="Localizador del Penetrador")

    # --- SALTO DE LÍNEA Y LÍNEA DE DIVISIÓN CONTINUA DE EXTREMO A EXTREMO ---
    st.markdown("<br>", unsafe_allow_html=True)
    st.divider()

    # Botón para finalizar examen posicionado debajo del divisor continuo
    if st.button("⚠️ FINALIZAR EXAMEN", key="btn_finalizar_directo"): 
        st.session_state.etapa = 'final'; st.rerun()

elif st.session_state.etapa in ['medir_d1', 'medir_d2']:
    eje = "H" if st.session_state.etapa == 'medir_d1' else "V"
    col_img, col_zoom, col_ctrl = st.columns([1.5, 1.5, 1])
    with col_ctrl:
        st.markdown("<h3 style='text-align: center;'>Ajuste de Reglilla</h3>", unsafe_allow_html=True)
        
        # Funciones de sincronización para que slider y botones hablen el mismo idioma
        def sync_l1(): st.session_state.l1 = st.session_state[f"reg_l1_{eje}"]
        def sync_l2(): st.session_state.l2 = st.session_state[f"reg_l2_{eje}"]

        # Definición de iconos según el eje
        if eje == "H":
            btn_menos, btn_mas = "◄", "►"
        else:
            btn_menos, btn_mas = "▲", "▼"

        # Definimos el incremento equivalente a 0.1 micrones adaptado a la nueva resolución (1600 / 2800)
        inc_01 = 1600 / 2800

        # Fila para Línea A
        ca1, ca2, ca3 = st.columns([1, 2, 1])
        if ca1.button(btn_menos, key="a_minus"): st.session_state.l1 -= inc_01
        with ca2: 
            st.markdown(f'<div style="background-color: #222; color: #00ff00; border: 1px solid #00ff00; font-weight: bold; text-align: center; padding: 5px; border-radius: 5px; height: 38px; line-height: 25px;">Línea A</div>', unsafe_allow_html=True)
        if ca3.button(btn_mas, key="a_plus"): st.session_state.l1 += inc_01

        # Fila para Línea B
        cb1, cb2, cb3 = st.columns([1, 2, 1])
        if cb1.button(btn_menos, key="b_minus"): st.session_state.l2 -= inc_01
        with cb2: 
            st.markdown(f'<div style="background-color: #222; color: #00ff00; border: 1px solid #00ff00; font-weight: bold; text-align: center; padding: 5px; border-radius: 5px; height: 38px; line-height: 25px;">Línea B</div>', unsafe_allow_html=True)
        if cb3.button(btn_mas, key="b_plus"): st.session_state.l2 += inc_01

        # Los sliders usan 'on_change' para actualizar la variable global al instante
                # Sliders con precisión estabilizada y formato de un decimal
                # Definición del rango basado en la visualización de la Lupa adaptativa para huellas grandes
        h_act = st.session_state.historial[-1]
        centro = h_act['pos'] if eje == "H" else h_act['pos']
        # --- AJUSTE DE RANGO COHERENTE PARA HUELLAS GRANDES ---
        h_act = st.session_state.historial[-1]
        ix, iy = h_act['pos']
        
        px_scale = 1600 / 280
        diametro_px = h_act['d_real'] * px_scale
        
        # Aplicamos exactamente la misma condición que en la lupa (Ventana = 1.5 * Diámetro) adaptado a 400px
        if diametro_px >= 400.0:
            z = (1.5 * diametro_px) / 2
        else:
            z = 200.0
        
        # Calculamos el centro visual de la lupa (con la lógica de bordes de obtener_zoom)
        centro_v = ix if eje == "H" else iy
        limite_pantalla = 1600 if eje == "H" else 1200
        
        l_izq = centro_v - z
        l_der = centro_v + z
        
        if l_izq < 0:
            l_der -= l_izq
            l_izq = 0
        if l_der > limite_pantalla:
            l_izq -= (l_der - limite_pantalla)
            l_der = limite_pantalla

        rango_min = float(l_izq)
        rango_max = float(l_der)

        # Slider Línea A
        st.slider("Línea A", rango_min, rango_max, float(st.session_state.l1), 
                  step=0.5714, format="%.1f", key=f"reg_l1_{eje}", on_change=sync_l1)
                  
        # Slider Línea B
        st.slider("Línea B", rango_min, rango_max, float(st.session_state.l2), 
                  step=0.5714, format="%.1f", key=f"reg_l2_{eje}", on_change=sync_l2)
        
        # Calculamos la lectura real y la mostramos con 1 decimal ajustando la escala a 1600 / 280
        lectura = abs(st.session_state.l1 - st.session_state.l2) / (1600 / 280)
        st.metric("LECTURA (μm)", f"{lectura:.1f}")
        
        if st.button("REGISTRAR"):
            img_full = renderizar_escena(True, eje)
            img_audit = obtener_zoom(img_full)
            if eje == "H":
                st.session_state.historial[-1]['cap_d1'] = img_audit
                st.session_state.historial[-1]['m_h'] = lectura
                st.session_state.etapa = 'medir_d2'
                pos_actual = st.session_state.historial[-1]['pos']
                # Reinicio de posición de reglillas para la siguiente medición (separación duplicada a 90 píxeles)
                st.session_state.l1, st.session_state.l2 = float(pos_actual[1]-90), float(pos_actual[1]+90)
            else:
                st.session_state.historial[-1]['cap_d2'] = img_audit
                st.session_state.historial[-1]['m_v'] = lectura
                st.session_state.etapa = 'preguntar'
            st.rerun()
            
        if st.button("⚠️ DESCARTAR"):
            img_full = renderizar_escena(False)
            st.session_state.historial[-1].update({'cap_def': obtener_zoom(img_full), 'descartada': True})
            st.session_state.etapa = 'preguntar'; st.rerun()
            
    img_m = renderizar_escena(True, eje)
    col_img.image(img_m, caption="Vista General")
    col_zoom.image(obtener_zoom(img_m), caption="Lupa")

elif st.session_state.etapa == 'preguntar':
    # Se limita el ancho de la imagen a 800 píxeles para mantener la estética compacta original en pantalla
    st.image(renderizar_escena(), width=800)
    c1, c2 = st.columns(2)
    if c1.button("NUEVA INDENTACIÓN"): st.session_state.etapa = 'ensayo'; st.rerun()
    if c2.button("⚠️ FINALIZAR EXAMEN"): st.session_state.etapa = 'final'; st.rerun()

elif st.session_state.etapa == 'final':
    st.header("🏁 REPORTE TÉCNICO DE COMPETENCIA")
    st.divider()
    
    img_distribucion = renderizar_escena(False)
    reporte_html = generar_html_reporte(img_distribucion)
    
    # Convertimos el reporte HTML a Base64 para permitir su descarga nativa
    b64_reporte = base64.b64encode(reporte_html.encode('utf-8')).decode()
    enlace_descarga = f'data:text/html;base64,{b64_reporte}'

    # Estructura del botón en HTML puro al 50% de ancho manteniendo la estética original de vértices y texto
    col_descarga_izq, col_descarga_der = st.columns(2)
    
    with col_descarga_izq:
        st.markdown(
            f"""
            <style>
            .btn-descarga-custom {{
                display: block;
                width: 100%;
                text-align: center;
                background-color: #00ff00;
                color: #000000 !important;
                border: 1px solid #00ff00;
                padding: 12px;
                font-family: 'Courier New', Courier, monospace;
                font-size: 16px;
                text-decoration: none;
                border-radius: 4px;
                transition: background-color 0.3s, color 0.3s;
                box-sizing: border-box;
            }}
            .btn-descarga-custom:hover {{
                background-color: #000000;
                color: #00ff00 !important;
                border: 1px solid #00ff00;
            }}
            </style>
            <a class="btn-descarga-custom" href="{enlace_descarga}" download="reporte_vickers_examen.html">
                📥 DESCARGAR REPORTE (HTML)
            </a>
            """,
            unsafe_allow_html=True
        )
    
    st.divider()
    st.subheader("📍 Vista General de Distribución (Huellas Realizadas)")
    st.image(img_distribucion, caption="Mapa de indentaciones en la probeta", width=900)
    st.divider()

    for i, h in enumerate(st.session_state.historial):
        st.subheader(f"Indentación ID: {i+1}")
        col_data, col_img1, col_img2 = st.columns([1, 1.5, 1.5])
        with col_data:
            st.write(f"**Carga:** {h['carga']} gf")
            st.write(f"**Tiempo:** {h['tiempo']} s")
            accion = "Descartada" if h['descartada'] else "Medida"
            st.write(f"**Operador:** {accion}")
            estado_txt = "Defectuosa" if h['defectuosa'] else "No defectuosa"
            st.write(f"**Estado:** {estado_txt}")
            if h['descartada']: st.write("**Medición [µm]:** n/a")
            else:
                st.write("**Medición [µm]:**")
                st.write(f"Horizontal: {h['m_h']:.1f}")
                st.write(f"Vertical: {h['m_v']:.1f}")
        if h['descartada']:
            if h['cap_def']: col_img1.image(h['cap_def'], caption="Captura al descartar")
        else:
            if h['cap_d1']: col_img1.image(h['cap_d1'], caption="Horizontal")
        if h['cap_d2']: col_img2.image(h['cap_d2'], caption="Vertical")
    st.divider()

    # --- DUPLICADO INFERIOR DEL BOTÓN DE DESCARGA ---
    col_descarga_inf_izq, col_descarga_inf_der = st.columns(2)
    with col_descarga_inf_izq:
        st.markdown(
            f"""
            <a class="btn-descarga-custom" href="{enlace_descarga}" download="reporte_vickers_examen.html">
                📥 DESCARGAR REPORTE (HTML)
            </a>
            """,
            unsafe_allow_html=True
        )
    st.divider()

    # Desempaquetamos las dos columnas nativas para estructurar los bloques individuales
    col_izq, col_der = st.columns(2)
    
    with col_izq:
        if st.button("CONTINUAR ENSAYO (MISMA PROBETA)", key="btn_misma_probeta"):
            # Se reanuda el simulador limpiando huellas pero MANTENIENDO la dureza_base original
            st.session_state.etapa = 'ensayo'
            st.session_state.historial = []
            st.session_state.temp_pos = (800, 600)
            # Nueva lógica de pool que respeta la regla del primer ensayo
            pool = [True, False, False, False, False]
            random.shuffle(pool)
            while pool[-1] == True: # Asegura que el primero en salir no sea True
                random.shuffle(pool)
            st.session_state.pool_defectos = pool
            st.rerun()
        # Falso botón deshabilitado que actúa como leyenda perfectamente alineada y centrada
        st.button("Se mantendrá el valor de dureza actual", key="lbl_misma_probeta", disabled=True)
        
    with col_der:
        if st.button("⚠️ FINALIZAR ENSAYO (CAMBIAR PROBETA)", key="btn_cambiar_probeta"):
            # Se reanuda el simulador limpiando huellas, la imagen cargada y ASIGNANDO una nueva dureza_base al azar
            st.session_state.etapa = 'ensayo'
            st.session_state.historial = []
            st.session_state.temp_pos = (800, 600)
            st.session_state.dureza_base = random.uniform(100, 300)
            st.session_state.img_original = obtener_img_base() # Limpia la imagen seleccionada volviendo a la base por defecto
            # Nueva lógica de pool que respeta la regla del primer ensayo
            pool = [True, False, False, False, False]
            random.shuffle(pool)
            while pool[-1] == True: # Asegura que el primero en salir no sea True
                random.shuffle(pool)
            st.session_state.pool_defectos = pool
            st.rerun()
        # Falso botón deshabilitado que actúa como leyenda perfectamente alineada y centrada
        st.button("Se asignará de forma aleatoria un valor de dureza nuevo", key="lbl_cambiar_probeta", disabled=True)
st.markdown(
    """
    <style>
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: rgba(14, 17, 23, 0.8); /* Fondo semi-transparente */
        color: #666;
        text-align: center;
        font-size: 9px;
        padding: 5px;
        font-family: 'Courier New', Courier, monospace;
        z-index: 999;
    }
    </style>
    <div class="footer">
        Copyright © 2026 Javier Paolantonio Guerrero | DNDA Reg. Nº: RL-2026-71651411-APN-DNDA#MJ
    </div>
    """,
    unsafe_allow_html=True
)