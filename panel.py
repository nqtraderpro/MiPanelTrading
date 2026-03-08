import time
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import calendar
import os
import warnings
warnings.filterwarnings('ignore')

# ==========================================
# 🔌 CONFIGURACIÓN MULTI-CUENTA GOOGLE DRIVE
# ==========================================
# Aquí están los IDs de tus dos cuentas de fondeo
IDS_DRIVE = ["1pnzJa0_Pupq0rP9XgOup2d2J7_OJVfd6", "1gXODXjDSf96Ggk-oGCsWOtSty-3YlOnP"]

st.set_page_config(page_title="Pro Trading Journal", layout="wide", initial_sidebar_state="expanded")
st.title("📊 Panel Cuantitativo Multi-Cuenta Institucional")

# ==========================================
# ==========================================
# INYECCIÓN DE TEMA: NAVEGANTE DEL CAOS
# ==========================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

/* Fondo principal y cuadrícula */
.stApp {
    background-color: #0a0e17;
    color: #e0e6ed;
    font-family: 'Inter', sans-serif;
}
.stApp::before {
    content: ''; position: fixed; inset: 0; pointer-events: none; z-index: 0; opacity: 0.04;
    background-image: linear-gradient(#00ffaa 1px, transparent 1px), linear-gradient(90deg, #00ffaa 1px, transparent 1px);
    background-size: 40px 40px;
}

/* Barra lateral oscura */
[data-testid="stSidebar"] {
    background-color: #0d1321 !important;
    border-right: 1px solid rgba(0,255,170,0.15);
}

/* Títulos estilo Terminal (SIN el !important en el color para respetar el rojo) */
h1, h2, h3, h4, h5, h6 {
    font-family: 'JetBrains Mono', monospace !important;
    color: #00ffaa;
    letter-spacing: 1px;
    text-shadow: 0 0 10px rgba(0,255,170,0.2);
}

/* Textos genéricos */
.stMarkdown p, .stText, label { 
    color: #e0e6ed; 
}

/* HACK: CAJAS DE TEXTO (INPUTS) Y BOTONES */
[data-baseweb="input"] {
    background-color: #0d1321 !important;
    border: 1px solid rgba(0,255,170,0.3) !important;
    border-radius: 4px !important;
}
[data-baseweb="input"] input {
    color: #00ffaa !important;
    font-family: 'JetBrains Mono', monospace !important;
}
.stButton button {
    background-color: rgba(0,255,170,0.1) !important;
    border: 1px solid #00ffaa !important;
    color: #00ffaa !important;
    font-family: 'JetBrains Mono', monospace !important;
    transition: all 0.3s ease;
}
.stButton button:hover {
    background-color: #00ffaa !important;
    color: #0a0e17 !important;
    box-shadow: 0 0 15px rgba(0,255,170,0.5) !important;
}

/* HACK: PESTAÑAS (TABS) */
[data-baseweb="tab-list"] { gap: 10px; }
[data-baseweb="tab"] {
    background-color: transparent !important;
    color: #5a6a7a !important;
    font-family: 'JetBrains Mono', monospace !important;
    border-bottom: 2px solid transparent !important;
}
[data-baseweb="tab"][aria-selected="true"] {
    color: #00d4ff !important;
    border-bottom-color: #00d4ff !important;
    background-color: rgba(0, 212, 255, 0.05) !important;
}

/* HACK: ALERTAS Y CAJAS INFO */
[data-testid="stAlert"] {
    background-color: rgba(13, 19, 33, 0.8) !important;
    border: 1px solid rgba(0, 212, 255, 0.3) !important;
    border-left: 4px solid #00d4ff !important;
    color: #e0e6ed !important;
}
</style>
""", unsafe_allow_html=True)
# =========================================================
# 🏆 INTERRUPTOR: MODO FONDEOS VS MODO TRADING
# =========================================================
import plotly.express as px

st.sidebar.markdown("---")
modo_panel = st.sidebar.radio("🎯 Selecciona la Vista:", ["📊 Trading Cuantitativo", "🏆 Gestión de Fondeos"])

import plotly.graph_objects as go

import plotly.graph_objects as go

if modo_panel == "🏆 Gestión de Fondeos":
    st.markdown("### 🏢 Mi Portfolio de Fondeos (Prop Firm Journey)")
    
    # --- 1. CONEXIÓN AL EXCEL DE FONDEOS ---
    ID_FONDEOS = "12fbo3yEsmollr5cUn6lj43hEKVa79p0vIgbYWQnBDGw"
    url_fondeos = f"https://docs.google.com/spreadsheets/d/{ID_FONDEOS}/export?format=csv"
    
    try:
        df_f = pd.read_csv(url_fondeos)
        
        # Limpieza de datos
        df_f['Fecha'] = pd.to_datetime(df_f['Fecha'], format='%d/%m/%Y', errors='coerce')
        df_f['Gasto'] = pd.to_numeric(df_f['Gasto'], errors='coerce').fillna(0)
        df_f['Beneficio'] = pd.to_numeric(df_f['Beneficio'], errors='coerce').fillna(0)
        df_f['Tamaño_Cuenta'] = pd.to_numeric(df_f['Tamaño_Cuenta'], errors='coerce').fillna(0)
        
        # --- MATEMÁTICAS DEL EMBUDO (KPIs) ---
        gastos_totales = df_f['Gasto'].sum()
        retiros_totales = df_f['Beneficio'].sum()
        pnl_neto = retiros_totales - gastos_totales
        
        # Estados (Detecta Fondeadas si el último evento fue 'Fondeado' o 'Retiro')
        ultimos_estados = df_f.sort_values('Fecha').groupby('ID_Cuenta').last()
        fondeadas_activas = ultimos_estados[ultimos_estados['Tipo_Evento'].isin(['Fondeado', 'Retiro'])]
        capital_actual = fondeadas_activas['Tamaño_Cuenta'].sum()
        
        # Ratios de Éxito (Basado en cuentas únicas para no inflar % si hay varios retiros)
        total_evaluaciones = df_f[df_f['Tipo_Evento'] == 'Compra']['ID_Cuenta'].nunique()
        cuentas_f1 = df_f[df_f['Tipo_Evento'] == 'Pase_Fase1']['ID_Cuenta'].nunique()
        cuentas_f2 = df_f[df_f['Tipo_Evento'] == 'Pase_Fase2']['ID_Cuenta'].nunique()
        cuentas_fondeadas = df_f[df_f['Tipo_Evento'] == 'Fondeado']['ID_Cuenta'].nunique()
        cuentas_retiro = df_f[df_f['Tipo_Evento'] == 'Retiro']['ID_Cuenta'].nunique()
        num_retiros = len(df_f[df_f['Tipo_Evento'] == 'Retiro']) # Total de retiros históricos
        
        tasa_f1 = (cuentas_f1 / total_evaluaciones * 100) if total_evaluaciones > 0 else 0
        tasa_f2 = (cuentas_f2 / total_evaluaciones * 100) if total_evaluaciones > 0 else 0 
        tasa_fondeo = (cuentas_fondeadas / total_evaluaciones * 100) if total_evaluaciones > 0 else 0
        tasa_retiro = (cuentas_retiro / total_evaluaciones * 100) if total_evaluaciones > 0 else 0
        
        # Colores dinámicos
        # Colores dinámicos
        pnl_color = "#00ffaa" if pnl_neto >= 0 else "#ff3366"

        # --- 2. DISEÑO CLONADO (MÉTRICAS PRINCIPALES) ---
        st.markdown(f"""
        <div style="display: flex; justify-content: space-between; text-align: center; margin-bottom: 15px;">
            <div style="background-color: #0d1321; padding: 20px; border-radius: 4px; width: 24%; border: 1px solid rgba(0,255,170,0.15); box-shadow: inset 0 0 20px rgba(0,255,170,0.02);">
                <p style="color: #00d4ff; font-size: 11px; margin:0; text-transform: uppercase; font-family: 'JetBrains Mono', monospace;">Capital Fondeado Actual</p>
                <h2 style="color: #00ffaa; margin:0; font-size: 32px; font-weight: bold; font-family: 'JetBrains Mono', monospace;">${capital_actual:,.0f}</h2>
            </div>
            <div style="background-color: #0d1321; padding: 20px; border-radius: 4px; width: 24%; border: 1px solid rgba(0,255,170,0.15); box-shadow: inset 0 0 20px rgba(0,255,170,0.02);">
                <p style="color: #00d4ff; font-size: 11px; margin:0; text-transform: uppercase; font-family: 'JetBrains Mono', monospace;">Retiros Totales</p>
                <h2 style="color: #00d4ff; margin:0; font-size: 32px; font-weight: bold; font-family: 'JetBrains Mono', monospace;">${retiros_totales:,.2f}</h2>
            </div>
            <div style="background-color: #0d1321; padding: 20px; border-radius: 4px; width: 24%; border: 1px solid rgba(0,255,170,0.15); box-shadow: inset 0 0 20px rgba(0,255,170,0.02);">
                <p style="color: #00d4ff; font-size: 11px; margin:0; text-transform: uppercase; font-family: 'JetBrains Mono', monospace;">Gasto en Pruebas</p>
                <h2 style="color: #ff3366; margin:0; font-size: 32px; font-weight: bold; font-family: 'JetBrains Mono', monospace;">-${gastos_totales:,.2f}</h2>
            </div>
            <div style="background-color: #0d1321; padding: 20px; border-radius: 4px; width: 24%; border: 1px solid rgba(0,255,170,0.15); box-shadow: inset 0 0 20px rgba(0,255,170,0.02);">
                <p style="color: #00d4ff; font-size: 11px; margin:0; text-transform: uppercase; font-family: 'JetBrains Mono', monospace;">Beneficio Neto (PnL)</p>
                <h2 style="color: {pnl_color}; margin:0; font-size: 32px; font-weight: bold; font-family: 'JetBrains Mono', monospace;">${pnl_neto:,.2f}</h2>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # --- SUB-MÉTRICAS (RATIOS Y EMBUDO AVANZADO) ---
        st.markdown(f"""
        <div style="display: flex; justify-content: space-between; text-align: center; margin-bottom: 30px;">
            <div style="background-color: #0d1321; padding: 10px; border-radius: 4px; width: 14%; border: 1px solid rgba(0,255,170,0.15);">
                <p style="color: #5a6a7a; font-size: 10px; margin:0; font-family: 'JetBrains Mono', monospace;">Cuentas Compradas</p>
                <h3 style="color: #e0e6ed; margin:0; font-size: 20px; font-family: 'JetBrains Mono', monospace;">{total_evaluaciones}</h3>
            </div>
            <div style="background-color: #0d1321; padding: 10px; border-radius: 4px; width: 14%; border: 1px solid rgba(0,255,170,0.15);">
                <p style="color: #5a6a7a; font-size: 10px; margin:0; font-family: 'JetBrains Mono', monospace;">Nº Payouts</p>
                <h3 style="color: #00ffaa; margin:0; font-size: 20px; font-family: 'JetBrains Mono', monospace;">{num_retiros}</h3>
            </div>
            <div style="background-color: #0d1321; padding: 10px; border-radius: 4px; width: 16%; border: 1px solid rgba(0,255,170,0.15);">
                <p style="color: #5a6a7a; font-size: 10px; margin:0; font-family: 'JetBrains Mono', monospace;">% Aprueba Fase 1</p>
                <h3 style="color: #e0e6ed; margin:0; font-size: 20px; font-family: 'JetBrains Mono', monospace;">{tasa_f1:.1f}%</h3>
            </div>
            <div style="background-color: #0d1321; padding: 10px; border-radius: 4px; width: 16%; border: 1px solid rgba(0,255,170,0.15);">
                <p style="color: #5a6a7a; font-size: 10px; margin:0; font-family: 'JetBrains Mono', monospace;">% Aprueba Fase 2</p>
                <h3 style="color: #e0e6ed; margin:0; font-size: 20px; font-family: 'JetBrains Mono', monospace;">{tasa_f2:.1f}%</h3>
            </div>
            <div style="background-color: #0d1321; padding: 10px; border-radius: 4px; width: 16%; border: 1px solid rgba(0,255,170,0.15);">
                <p style="color: #5a6a7a; font-size: 10px; margin:0; font-family: 'JetBrains Mono', monospace;">% Llegan a Fondeo</p>
                <h3 style="color: #00d4ff; margin:0; font-size: 20px; font-family: 'JetBrains Mono', monospace;">{tasa_fondeo:.1f}%</h3>
            </div>
            <div style="background-color: #0d1321; padding: 10px; border-radius: 4px; width: 16%; border: 1px solid rgba(0,255,170,0.15);">
                <p style="color: #5a6a7a; font-size: 10px; margin:0; font-family: 'JetBrains Mono', monospace;">% Llegan a Cobrar</p>
                <h3 style="color: #00ffaa; margin:0; font-size: 20px; font-family: 'JetBrains Mono', monospace;">{tasa_retiro:.1f}%</h3>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # --- 3. GRÁFICOS INSTITUCIONALES (FILA 1) ---
        st.markdown("---")
        col1, col2, col3 = st.columns([1.2, 1.5, 1])
        
        with col1:
            st.markdown("###### 📜 Historial de Eventos")
            st.dataframe(df_f[['Fecha', 'Tipo_Evento', 'Tamaño_Cuenta', 'Empresa', 'Gasto', 'Beneficio']].sort_values('Fecha', ascending=False), use_container_width=True, hide_index=True, height=250)
            
        with col2:
            st.markdown("###### 📈 Curva de PnL (Beneficio Neto)")
            df_pnl = df_f.sort_values('Fecha').copy()
            df_pnl['Flujo'] = df_pnl['Beneficio'] - df_pnl['Gasto']
            df_pnl['PnL_Acumulado'] = df_pnl['Flujo'].cumsum()
            fig_pnl = px.line(df_pnl, x='Fecha', y='PnL_Acumulado', markers=True, template="simple_white")
            fig_pnl.update_traces(line_color='#007bff', line_width=3, marker_size=8)
            fig_pnl.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=250, yaxis_title="USD", xaxis_title="")
            st.plotly_chart(fig_pnl, use_container_width=True)
            
        with col3:
            st.markdown("###### 🍩 Evaluaciones por Tamaño")
            df_compras = df_f[df_f['Tipo_Evento'] == 'Compra']
            if not df_compras.empty:
                fig_donut = px.pie(df_compras, names='Tamaño_Cuenta', hole=0.6, template="simple_white")
                fig_donut.update_traces(textinfo='percent+label')
                fig_donut.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=250, showlegend=False)
                st.plotly_chart(fig_donut, use_container_width=True)
            else:
                st.info("Sin datos suficientes.")

        # --- 4. GRÁFICOS INSTITUCIONALES (FILA 2 - RENDIMIENTO POR EMPRESA) ---
        st.markdown("---")
        col4, col5 = st.columns(2)

        with col4:
            st.markdown("###### ⚖️ Gastos vs Retiros por Prop Firm")
            df_grouped = df_f.groupby('Empresa')[['Gasto', 'Beneficio']].sum().reset_index()
            df_grouped['Gasto_Negativo'] = -df_grouped['Gasto'] 
            
            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(y=df_grouped['Empresa'], x=df_grouped['Gasto_Negativo'], name='Gasto en Pruebas', orientation='h', marker_color='#dc3545'))
            fig_bar.add_trace(go.Bar(y=df_grouped['Empresa'], x=df_grouped['Beneficio'], name='Retiros', orientation='h', marker_color='#007bff'))
            fig_bar.update_layout(barmode='relative', template="simple_white", margin=dict(l=0, r=0, t=10, b=0), height=300, legend=dict(orientation="h", y=-0.2, yanchor="top"))
            st.plotly_chart(fig_bar, use_container_width=True)

        with col5:
            st.markdown("###### 🎯 Fase Alcanzada por Empresa (%)")
            eventos_clave = ['Compra', 'Pase_Fase1', 'Pase_Fase2', 'Fondeado', 'Retiro']
            df_fases = df_f[df_f['Tipo_Evento'].isin(eventos_clave)]
            
            if not df_fases.empty:
                # Lógica para determinar el máximo estado alcanzado por cada cuenta
                fase_maxima = df_fases.groupby(['Empresa', 'ID_Cuenta'])['Tipo_Evento'].apply(
                    lambda x: 'Fondeada/Retiro' if ('Fondeado' in x.values or 'Retiro' in x.values) 
                    else ('Fase 3 (Verificación)' if 'Pase_Fase2' in x.values 
                    else ('Fase 2' if 'Pase_Fase1' in x.values else 'Fase 1'))
                ).reset_index()
                
                resumen_fases = fase_maxima.groupby(['Empresa', 'Tipo_Evento']).size().reset_index(name='Cantidad')
                
                fig_stack = px.bar(resumen_fases, y="Empresa", x="Cantidad", color="Tipo_Evento", orientation='h', 
                                   color_discrete_map={'Fase 1': '#a0c4ff', 'Fase 2': '#4a90e2', 'Fase 3 (Verificación)': '#005bb5', 'Fondeada/Retiro': '#003366'}, 
                                   template="simple_white")
                fig_stack.update_layout(barmode='stack', barnorm='percent', margin=dict(l=0, r=0, t=10, b=0), height=300, legend_title="", legend=dict(orientation="h", y=-0.2, yanchor="top"))
                fig_stack.update_xaxes(title_text="% Alcanzado")
                st.plotly_chart(fig_stack, use_container_width=True)
            else:
                st.info("Registra compras y pases de fase para ver este gráfico.")

    except Exception as e:
        st.warning(f"⚠️ Esperando conexión o datos en el Excel... (Error: {e})")
        
    st.stop()
# =========================================================
# (El resto de tu código original sigue aquí abajo, intacto)
# Función para descargar todas las cuentas y fusionarlas (Actualiza cada 10 min)

def cargar_datos_automaticos():
    lista_dfs = []
    for id_doc in IDS_DRIVE:
        url = f'https://drive.google.com/uc?id={id_doc}&t={time.time()}'
        try:
            df_temp = pd.read_csv(url, encoding='latin1')
            lista_dfs.append(df_temp)
        except Exception as e:
            pass # Si falla uno, intenta con el siguiente
            
    if lista_dfs:
        return pd.concat(lista_dfs, ignore_index=True)
    return None

try:
    # ==========================================
    # 0. SISTEMA DE CARPETAS (Diario Local)
    # ==========================================
    if not os.path.exists("Diario_Trading"): os.makedirs("Diario_Trading")
    if not os.path.exists("Diario_Trading/Screenshots"): os.makedirs("Diario_Trading/Screenshots")

    # ==========================================
    # 1. CARGA AUTOMÁTICA
    # ==========================================
    st.sidebar.markdown("### 🛰️ Estado de Conexión")
    df_raw = cargar_datos_automaticos()

    if df_raw is None or df_raw.empty:
        st.error("⚠️ **No se pudieron leer los archivos de Google Drive.**\nVerifica que los archivos estén configurados como 'Cualquier persona con el enlace' (Lector).")
        st.stop()
    else:
        st.sidebar.success("✅ Cuentas sincronizadas en tiempo real")
        if st.sidebar.button("🔄 Forzar Actualización"):
            st.cache_data.clear()
            st.rerun()

    df = df_raw.drop_duplicates()
    
    if 'Cuenta' not in df.columns:
        st.error("⚠️ Los archivos en Drive no tienen el formato correcto de MetaTrader.")
        st.stop()

    df['Cuenta'] = df['Cuenta'].astype(str).str.replace(".0", "", regex=False)

    col_fecha, col_simbolo, col_tipo, col_beneficio = df.columns[2], df.columns[3], df.columns[4], df.columns[6]
    col_volumen = df.columns[5]

    # --- 🛠️ TRADUCTOR DEL HISTORIAL MANUAL (MYFXBOOK) ---
    # 1. Traducimos las columnas PRIMERO
    if 'Beneficio (USD)' in df.columns:
        df[col_beneficio] = df[col_beneficio].fillna(pd.to_numeric(df['Beneficio (USD)'], errors='coerce'))
        
    if 'Cuenta' not in df.columns:
        df['Cuenta'] = None
    df['Cuenta'] = df['Cuenta'].fillna('Historial_2_Años')
        
    if 'Acción' in df.columns:
        df[col_tipo] = df[col_tipo].fillna(df['Acción'])
        
    if 'Símbolo' in df.columns:
        df[col_simbolo] = df[col_simbolo].fillna(df['Símbolo'])
        
    if 'Fecha de cierre' in df.columns:
        df[col_fecha] = df[col_fecha].fillna(df['Fecha de cierre'])

    if col_tipo in df.columns:
        df[col_tipo] = df[col_tipo].astype(str).str.lower().replace({
            'comprar': 'buy', 'vender': 'sell', 'buy': 'buy', 'sell': 'sell'
        })

    # 2. AHORA SÍ: Filtramos las que estén vacías (El "portero")
    df[col_beneficio] = pd.to_numeric(df[col_beneficio], errors='coerce')
    df = df.dropna(subset=[col_beneficio])
    # --------------------------------------------------------

    # ==========================================
    # 2. GESTIÓN MULTI-CUENTA
    # ==========================================
    st.sidebar.markdown("---")
    st.sidebar.header("⚙️ Gestión de Cuentas")

    # Eliminamos posibles vacíos y creamos el menú
    df = df.dropna(subset=['Cuenta'])
    cuentas_detectadas = list(df['Cuenta'].unique())
    cuenta_seleccionada = st.sidebar.selectbox("📂 Seleccionar Cuenta:", ["Todas las Cuentas (Consolidado)"] + cuentas_detectadas)

    if cuenta_seleccionada != "Todas las Cuentas (Consolidado)":
        df = df[df['Cuenta'] == cuenta_seleccionada]
    # ==========================================
    # 3. CAPITAL, RETIROS Y COSTES
    # ==========================================
    depositos_df = df[(df[col_simbolo].isna()) | (df[col_tipo].astype(str).str.lower() == 'balance')]
    balance_detectado = depositos_df[depositos_df[col_beneficio] > 0][col_beneficio].sum()
    if balance_detectado <= 0: balance_detectado = 50000.0

    # === VARIABLES INTERNAS (Menú lateral ocultado) ===
    balance_inicial = balance_detectado
    retiros_acumulados = abs(depositos_df[depositos_df[col_beneficio] < 0][col_beneficio].sum())
    coste_pruebas = 0
    beneficio_neto_real = retiros_acumulados - coste_pruebas
    # ==========================================
    # MIS REGLAS DE TRADING EN SIDEBAR
    # ==========================================
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📜 Mis Reglas de Trading")
    archivo_reglas = "Diario_Trading/mis_reglas.txt"
    
    if os.path.exists(archivo_reglas):
        with open(archivo_reglas, "r", encoding="utf-8") as f:
            reglas_guardadas = f.read()
    else:
        reglas_guardadas = "1. No operar noticias de alto impacto.\n2. Riesgo máximo por trade: 1%.\n3. Máximo 2 pérdidas seguidas al día.\n4. Si cumplo mi plan, el día es exitoso."
        
    mis_reglas = st.sidebar.text_area("Escribe y guarda tus reglas base:", value=reglas_guardadas, height=180)
    if st.sidebar.button("💾 Guardar Reglas"):
        with open(archivo_reglas, "w", encoding="utf-8") as f:
            f.write(mis_reglas)
        st.sidebar.success("¡Reglas blindadas!")

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🚀 Simulador de Crecimiento")
    objetivo_mensual = st.sidebar.slider("Objetivo Mensual (%)", 1, 20, 5)
    años_proyeccion = st.sidebar.slider("Años a proyectar", 1, 10, 3)

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🖨️ Exportar Informe")
    st.sidebar.info("Para generar el **PDF Profesional**, pulsa **Cmd + P** en tu teclado y dale a 'Guardar como PDF'.")

    # ==========================================
    # 4. LIMPIEZA DE FECHAS Y SESIONES
    # ==========================================
    df['Cierre'] = pd.to_datetime(df[col_fecha], format='%Y.%m.%d %H:%M', errors='coerce')
    if df['Cierre'].isna().all(): df['Cierre'] = pd.to_datetime(df[col_fecha], errors='coerce')
        
    df['Fecha'] = df['Cierre'].dt.date
    df['Año'] = df['Cierre'].dt.year
    df['Mes_Num'] = df['Cierre'].dt.month
    df['Dia_Num'] = df['Cierre'].dt.dayofweek
    df['Hora_Dia'] = df['Cierre'].dt.hour
    df['Mes_Año_Sort'] = df['Cierre'].dt.to_period('M')
    
    dias_map = {0:'Lunes', 1:'Martes', 2:'Miércoles', 3:'Jueves', 4:'Viernes', 5:'Sábado', 6:'Domingo'}
    df['Dia_Semana'] = df['Dia_Num'].map(dias_map)
    df = df.dropna(subset=['Fecha']).sort_values('Cierre')

    def asignar_sesion(hora):
        if 1 <= hora < 9: return "Asia"
        elif 9 <= hora < 15: return "Londres"
        elif 15 <= hora < 22: return "Nueva York"
        else: return "Cierre/Otra"
    df['Sesion'] = df['Hora_Dia'].apply(asignar_sesion)

   # ==========================================
    # 5. MATEMÁTICAS AVANZADAS (FILTRO MT5 INCLUIDO)
    # ==========================================
    # 1º La gráfica suma todo: el depósito inicial de MT5, las operaciones y resta los retiros.
    df['Equidad_Acumulada'] = df[col_beneficio].cumsum()

    # 2º LIMPIAMOS LOS DATOS para sacar las estadísticas de trading puro
    df_trades = df[(df[col_simbolo].notna()) & (df[col_tipo].astype(str).str.lower() != 'balance')].copy()

    # Filtramos operaciones a cero (Entradas de MT5)
    df_trades = df_trades[df_trades[col_beneficio] != 0]

    if df_trades.empty:
        st.info("Aún no hay operaciones reales registradas.")
        st.stop()
    df_trades['Equidad_Pico'] = df_trades['Equidad_Acumulada'].cummax()
    df_trades['Drawdown_$'] = df_trades['Equidad_Acumulada'] - df_trades['Equidad_Pico']
    
    max_drawdown_dinero = abs(df_trades['Drawdown_$'].min())
    df_trades['Drawdown_%'] = (abs(df_trades['Drawdown_$']) / df_trades['Equidad_Pico']) * 100
    max_drawdown_pct = df_trades['Drawdown_%'].max()

    df_trades['Equidad_Anterior'] = df_trades['Equidad_Acumulada'].shift(1).fillna(balance_inicial)
    df_trades['Porcentaje_Trade'] = (df_trades[col_beneficio] / df_trades['Equidad_Anterior']) * 100
    df_trades['Resultado'] = df_trades[col_beneficio].apply(lambda x: 'Ganancia' if x > 0 else 'Pérdida')

    df_trades['Es_Ganadora'] = df_trades[col_beneficio] > 0
    df_trades['Bloque_Racha'] = (df_trades['Es_Ganadora'] != df_trades['Es_Ganadora'].shift()).cumsum()
    rachas = df_trades.groupby(['Es_Ganadora', 'Bloque_Racha']).size()
    max_racha_win = rachas[True].max() if True in rachas else 0
    max_racha_loss = rachas[False].max() if False in rachas else 0

    compras = df_trades[df_trades[col_tipo].astype(str).str.lower() == 'buy']
    ventas = df_trades[df_trades[col_tipo].astype(str).str.lower() == 'sell']
    wr_compras = (len(compras[compras[col_beneficio]>0])/len(compras)*100) if len(compras)>0 else 0
    wr_ventas = (len(ventas[ventas[col_beneficio]>0])/len(ventas)*100) if len(ventas)>0 else 0

    beneficio_total = df_trades[col_beneficio].sum()
    total_trades = len(df_trades)
    ganadoras = df_trades[df_trades[col_beneficio] > 0]
    perdedoras = df_trades[df_trades[col_beneficio] < 0]
    
    win_rate = (len(ganadoras) / total_trades) * 100 if total_trades > 0 else 0
    profit_factor = ganadoras[col_beneficio].sum() / abs(perdedoras[col_beneficio].sum()) if abs(perdedoras[col_beneficio].sum()) > 0 else ganadoras[col_beneficio].sum()
    
    avg_win = ganadoras[col_beneficio].mean() if len(ganadoras) > 0 else 0
    avg_loss = perdedoras[col_beneficio].mean() if len(perdedoras) > 0 else 0
    expectancia = beneficio_total / total_trades if total_trades > 0 else 0
    
    win_rate_dec = len(ganadoras) / total_trades if total_trades > 0 else 0
    risk_reward_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else 1
    kelly_pct = (win_rate_dec - ((1 - win_rate_dec) / risk_reward_ratio)) * 100 if risk_reward_ratio > 0 else 0
    kelly_pct = max(0, kelly_pct)

    if expectancia > 0:
        riesgo_ruina = "Bajo ✅"
    else:
        riesgo_ruina = "Alto ⚠️"

    # ==========================================
    # MÉTRICAS QUANTS INSTITUCIONALES Y RADAR
    # ==========================================
    recovery_factor = beneficio_total / max_drawdown_dinero if max_drawdown_dinero > 0 else 0
    
    if total_trades > 1:
        std_profit = df_trades[col_beneficio].std()
        sqn = (expectancia / std_profit) * np.sqrt(total_trades) if std_profit > 0 else 0
        
        pct_returns = df_trades['Porcentaje_Trade']
        std_pct = pct_returns.std()
        sharpe = (pct_returns.mean() / std_pct) * np.sqrt(total_trades) if std_pct > 0 else 0
        
        downside_returns = pct_returns[pct_returns < 0]
        downside_std = downside_returns.std() if len(downside_returns) > 1 else 0.0001
        sortino = (pct_returns.mean() / downside_std) * np.sqrt(total_trades) if downside_std > 0 else 0
    else:
        sqn, sharpe, sortino = 0, 0, 0

    score_wr = min(100, win_rate * 2) 
    score_pf = min(100, profit_factor * 40) if profit_factor > 0 else 0 
    score_rr = min(100, risk_reward_ratio * 33.3) 
    score_dd = max(0, 100 - (max_drawdown_pct * 10)) 
    score_kelly = min(100, kelly_pct * 10) 
    score_cons = max(0, 100 - (max_racha_loss * 5)) 
    categorias_radar = ['Win Rate', 'Profit Factor', 'Risk / Reward', 'Control Drawdown', 'Supervivencia', 'Consistencia']
    puntuaciones_radar = [score_wr, score_pf, score_rr, score_dd, score_kelly, score_cons]
    puntuacion_global = np.mean(puntuaciones_radar)

    # ==========================================
    # 6. RESUMEN RÁPIDO Y KPIs
    # ==========================================
    st.markdown("### ⏱️ Resumen de Rendimiento (Un Vistazo)")
    ultima_fecha = pd.to_datetime(df_trades['Cierre'].max())
    df_año = df_trades[df_trades['Año'] == ultima_fecha.year]
    df_mes = df_año[df_año['Mes_Num'] == ultima_fecha.month]
    df_semana = df_año[df_año['Cierre'].dt.isocalendar().week == ultima_fecha.isocalendar().week]

    pnl_año = df_año[col_beneficio].sum()
    pnl_mes = df_mes[col_beneficio].sum()
    pnl_semana = df_semana[col_beneficio].sum()

    eq_ini_año = df_año['Equidad_Anterior'].iloc[0] if len(df_año)>0 else balance_inicial
    eq_ini_mes = df_mes['Equidad_Anterior'].iloc[0] if len(df_mes)>0 else balance_inicial
    eq_ini_semana = df_semana['Equidad_Anterior'].iloc[0] if len(df_semana)>0 else balance_inicial

    pct_año = (pnl_año / eq_ini_año) * 100
    pct_mes = (pnl_mes / eq_ini_mes) * 100
    pct_semana = (pnl_semana / eq_ini_semana) * 100

    # Colores dinámicos
    c_sem = "#00ffaa" if pnl_semana >= 0 else "#ff3366"
    c_mes = "#00ffaa" if pnl_mes >= 0 else "#ff3366"
    c_ano = "#00ffaa" if pnl_año >= 0 else "#ff3366"
    c_neto = "#00ffaa" if beneficio_total >= 0 else "#ff3366"
    c_dd = "#ff3366" if max_drawdown_dinero > 0 else "#00ffaa"

    st.markdown(f"""
    <div style="display: flex; gap: 15px; margin-bottom: 25px; flex-wrap: wrap;">
        <div style="flex: 1; min-width: 200px; background-color: #0d1321; padding: 20px; border-radius: 4px; border: 1px solid rgba(0,255,170,0.15); box-shadow: inset 0 0 20px rgba(0,255,170,0.02);">
            <p style="color: #00d4ff; font-size: 11px; margin:0; text-transform: uppercase; font-family: 'JetBrains Mono', monospace;">ESTA SEMANA</p>
            <h2 style="color: {c_sem}; margin:8px 0 0 0; font-size: 32px; font-weight: bold; font-family: 'JetBrains Mono', monospace; text-shadow: 0 0 8px {c_sem}40;">${pnl_semana:,.2f}</h2>
            <span style="color: {c_sem}; font-size: 13px; font-family: 'JetBrains Mono', monospace;">{pct_semana:+.2f}%</span>
        </div>
        <div style="flex: 1; min-width: 200px; background-color: #0d1321; padding: 20px; border-radius: 4px; border: 1px solid rgba(0,255,170,0.15); box-shadow: inset 0 0 20px rgba(0,255,170,0.02);">
            <p style="color: #00d4ff; font-size: 11px; margin:0; text-transform: uppercase; font-family: 'JetBrains Mono', monospace;">ESTE MES</p>
            <h2 style="color: {c_mes}; margin:8px 0 0 0; font-size: 32px; font-weight: bold; font-family: 'JetBrains Mono', monospace; text-shadow: 0 0 8px {c_mes}40;">${pnl_mes:,.2f}</h2>
            <span style="color: {c_mes}; font-size: 13px; font-family: 'JetBrains Mono', monospace;">{pct_mes:+.2f}%</span>
        </div>
        <div style="flex: 1; min-width: 200px; background-color: #0d1321; padding: 20px; border-radius: 4px; border: 1px solid rgba(0,255,170,0.15); box-shadow: inset 0 0 20px rgba(0,255,170,0.02);">
            <p style="color: #00d4ff; font-size: 11px; margin:0; text-transform: uppercase; font-family: 'JetBrains Mono', monospace;">ESTE AÑO</p>
            <h2 style="color: {c_ano}; margin:8px 0 0 0; font-size: 32px; font-weight: bold; font-family: 'JetBrains Mono', monospace; text-shadow: 0 0 8px {c_ano}40;">${pnl_año:,.2f}</h2>
            <span style="color: {c_ano}; font-size: 13px; font-family: 'JetBrains Mono', monospace;">{pct_año:+.2f}%</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    
    st.markdown(f"""
    <div style="display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap;">
        <div style="flex: 1; min-width: 140px; background-color: #0d1321; padding: 15px; border-radius: 4px; border: 1px solid rgba(0,255,170,0.15);">
            <p style="color: #5a6a7a; font-size: 10px; margin:0; font-family: 'JetBrains Mono', monospace; text-transform: uppercase;">Beneficio Neto</p>
            <h2 style="color: {c_neto}; margin:5px 0 0 0; font-size: 22px; font-family: 'JetBrains Mono', monospace;">${beneficio_total:,.2f}</h2>
        </div>
        <div style="flex: 1; min-width: 140px; background-color: #0d1321; padding: 15px; border-radius: 4px; border: 1px solid rgba(0,255,170,0.15);">
            <p style="color: #5a6a7a; font-size: 10px; margin:0; font-family: 'JetBrains Mono', monospace; text-transform: uppercase;">Win Rate</p>
            <h2 style="color: #e0e6ed; margin:5px 0 0 0; font-size: 22px; font-family: 'JetBrains Mono', monospace;">{win_rate:.1f}%</h2>
        </div>
        <div style="flex: 1; min-width: 140px; background-color: #0d1321; padding: 15px; border-radius: 4px; border: 1px solid rgba(0,255,170,0.15);">
            <p style="color: #5a6a7a; font-size: 10px; margin:0; font-family: 'JetBrains Mono', monospace; text-transform: uppercase;">Profit Factor</p>
            <h2 style="color: #e0e6ed; margin:5px 0 0 0; font-size: 22px; font-family: 'JetBrains Mono', monospace;">{profit_factor:.2f}</h2>
        </div>
        <div style="flex: 1; min-width: 140px; background-color: #0d1321; padding: 15px; border-radius: 4px; border: 1px solid rgba(0,255,170,0.15);">
            <p style="color: #5a6a7a; font-size: 10px; margin:0; font-family: 'JetBrains Mono', monospace; text-transform: uppercase;">Max Drawdown</p>
            <h2 style="color: {c_dd}; margin:5px 0 0 0; font-size: 22px; font-family: 'JetBrains Mono', monospace;">-${max_drawdown_dinero:,.2f}</h2>
            <span style="color: {c_dd}; font-size: 11px; font-family: 'JetBrains Mono', monospace;">-{max_drawdown_pct:.2f}%</span>
        </div>
        <div style="flex: 1; min-width: 140px; background-color: #0d1321; padding: 15px; border-radius: 4px; border: 1px solid rgba(0,255,170,0.15);">
            <p style="color: #5a6a7a; font-size: 10px; margin:0; font-family: 'JetBrains Mono', monospace; text-transform: uppercase;">Total Trades</p>
            <h2 style="color: #e0e6ed; margin:5px 0 0 0; font-size: 22px; font-family: 'JetBrains Mono', monospace;">{total_trades}</h2>
        </div>
    </div>
    """, unsafe_allow_html=True)
    # ==========================================
    # 7. BLOQUE INSTITUCIONAL Y ESTADÍSTICAS BASE
    # ==========================================
    st.markdown("---")
    st.markdown("### 🏦 Nivel Institucional (Quants)")
    col_q1, col_q2, col_q3, col_q4 = st.columns(4)
    
    with col_q1:
        st.write("**Factor de Recuperación:**")
        st.subheader(f"{recovery_factor:.2f}")
        st.caption("Ideal > 2.0")
    with col_q2:
        st.write("**SQN (Van Tharp):**")
        st.subheader(f"{sqn:.2f}")
        st.caption("Ideal > 2.0 (Excelente > 3)")
    with col_q3:
        st.write("**Ratio Sharpe:**")
        st.subheader(f"{sharpe:.2f}")
        st.caption("Ideal > 1.0 (Riesgo general)")
    with col_q4:
        st.write("**Ratio Sortino:**")
        st.subheader(f"{sortino:.2f}")
        st.caption("Ideal > 1.5 (Riesgo negativo)")

    st.markdown("---")
    col_r1, col_r2, col_r3 = st.columns(3)
    with col_r1:
        st.markdown("### 🧮 Supervivencia")
        st.info(f"**Criterio de Kelly:** Arriesgar máximo **{kelly_pct:.1f}%** por trade.")
        st.write(f"**Riesgo de Ruina:** {riesgo_ruina}")
    with col_r2:
        st.markdown("### ⚖️ Estadísticas Base")
        st.write(f"**Expectancia:** ${expectancia:,.2f} / trade")
        st.write(f"**Promedio Ganancia:** ${avg_win:,.2f}")
        st.write(f"**Promedio Pérdida:** ${avg_loss:,.2f}")
    with col_r3:
        st.markdown("### 🏆 Rendimiento Operativo")
        st.write(f"**Total Operaciones:** {total_trades}")
        st.write(f"**Ratio Riesgo/Beneficio:** 1 : {risk_reward_ratio:.2f}")

    st.markdown("---")
    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    with col_s1:
        st.markdown("### 🟢 Rachas")
        st.write(f"🔥 **Ganadoras seguidas:** {max_racha_win}")
        st.write(f"🧊 **Perdedoras seguidas:** {max_racha_loss}")
    with col_s2:
        st.markdown("### 🛒 Direccionalidad")
        st.write(f"📈 **Compras:** {len(compras)} ops ({wr_compras:.1f}% Acierto)")
        st.write(f"📉 **Ventas:** {len(ventas)} ops ({wr_ventas:.1f}% Acierto)")
    with col_s3:
        st.markdown("### 🌍 Sesiones")
        df_sesion = df_trades.groupby('Sesion').agg(Ops=(col_beneficio, 'count'), PnL=(col_beneficio, 'sum')).reset_index()
        for _, row in df_sesion.iterrows():
            st.write(f"**{row['Sesion']}:** {row['Ops']} ops | ${row['PnL']:.0f}")
    with col_s4:
        st.markdown("### 📊 Activos (Símbolos)")
        df_activos = df_trades.groupby(col_simbolo).agg(Ops=(col_beneficio, 'count'), PnL=(col_beneficio, 'sum')).reset_index()
        for _, row in df_activos.iterrows():
            icono = "🟩" if row['PnL'] > 0 else "🟥"
            st.write(f"{icono} **{row[col_simbolo]}:** ${row['PnL']:.0f} ({row['Ops']} ops)")

    st.markdown("---")

    # ==========================================
    # 8. GRÁFICOS: EQUIDAD Y DÍAS DE LA SEMANA
    # ==========================================
    col_graf_izq, col_graf_der = st.columns([2, 1])

    with col_graf_izq:
        st.markdown(f"### 📈 Curva de Equidad ({cuenta_seleccionada})")
        fig_equity = go.Figure()
        fig_equity.add_trace(go.Scatter(x=df_trades['Cierre'], y=df_trades['Equidad_Pico'], mode='lines', line=dict(width=0), showlegend=False, hoverinfo='skip'))
        fig_equity.add_trace(go.Scatter(x=df_trades['Cierre'], y=df_trades['Equidad_Acumulada'], mode='lines', 
                                        fill='tonexty', fillcolor='rgba(255, 77, 77, 0.3)', 
                                        name='Equidad', line=dict(color='#00bfff', width=3)))
        min_y = min(balance_inicial - max_drawdown_dinero, df_trades['Equidad_Acumulada'].min()) * 0.99
        fig_equity.update_layout(template="plotly_dark", hovermode="x unified", margin=dict(l=0, r=0, t=30, b=0), yaxis=dict(range=[min_y, None]))
        st.plotly_chart(fig_equity, use_container_width=True)

    with col_graf_der:
        st.markdown("### 📅 Rendimiento por Día")
        df_dias = df_trades.groupby(['Dia_Num', 'Dia_Semana'])[col_beneficio].sum().reset_index().sort_values('Dia_Num')
        df_dias['Color'] = df_dias[col_beneficio].apply(lambda x: '#00cc66' if x > 0 else '#ff4d4d')
        fig_dias = go.Figure(data=[go.Bar(x=df_dias['Dia_Semana'], y=df_dias[col_beneficio], marker_color=df_dias['Color'], text=df_dias[col_beneficio].apply(lambda x: f"${x:,.0f}"), textposition='auto')])
        fig_dias.update_layout(template="plotly_dark", margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig_dias, use_container_width=True)

    st.markdown("---")

    # ==========================================
    # 9. SCATTER PLOT Y RADAR DE PUNTUACIÓN
    # ==========================================
    col_scatter, col_radar = st.columns([2.5, 1.5])
    
    with col_scatter:
        st.markdown("### ⏱️ Análisis Operativo: Hora de Ejecución")
        fig_scatter = px.scatter(
            df_trades, x='Hora_Dia', y='Porcentaje_Trade', color='Resultado',
            color_discrete_map={'Ganancia': '#00cc66', 'Pérdida': '#ff4d4d'},
            symbol='Resultado', symbol_map={'Ganancia': 'diamond', 'Pérdida': 'circle'},
            hover_data={'Hora_Dia': ':.0f', 'Porcentaje_Trade': ':.2f', col_beneficio: ':.2f'},
            labels={'Hora_Dia': 'Hora del Día', 'Porcentaje_Trade': 'Crecimiento (%)'}
        )
        fig_scatter.update_traces(marker=dict(size=12, opacity=0.8, line=dict(width=1, color='DarkSlateGrey')))
        fig_scatter.update_layout(template="plotly_dark", margin=dict(l=0, r=0, t=30, b=0), height=350, xaxis=dict(tickmode='linear', tick0=0, dtick=1))
        st.plotly_chart(fig_scatter, use_container_width=True)

    with col_radar:
        st.markdown("### 🎯 Trader Score Global")
        df_radar = pd.DataFrame(dict(r=puntuaciones_radar + [puntuaciones_radar[0]], theta=categorias_radar + [categorias_radar[0]]))
        
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=df_radar['r'], theta=df_radar['theta'],
            fill='toself', fillcolor='rgba(0, 204, 102, 0.4)',
            line=dict(color='#00e676', width=2), name='Score'
        ))
        
        fig_radar.update_layout(
            template="plotly_dark",
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 100], color='#888', gridcolor='#333'),
                angularaxis=dict(gridcolor='#444')
            ),
            showlegend=False,
            margin=dict(l=40, r=40, t=20, b=20),
            height=280
        )
        st.plotly_chart(fig_radar, use_container_width=True)
        
        color_score = "#00e676" if puntuacion_global >= 60 else "#ffcc00" if puntuacion_global >= 40 else "#ff4d4d"
        st.markdown(f"<h1 style='text-align: center; color: {color_score}; font-size: 48px; margin-top: -30px;'>{puntuacion_global:.1f} / 100</h1>", unsafe_allow_html=True)

    st.markdown("---")

    # ==========================================
    # 10. MENSUAL (%) y ZONA DE CALENDARIOS
    # ==========================================
    col_mes, col_cal = st.columns([1.2, 1.5])

# ==========================================
    # WIDGET: RIESGO CUANTITATIVO Y VENTAJA ESTADÍSTICA (EDGE)
    # ==========================================
    if 'balance_inicial' in locals() and balance_inicial > 0 and 'win_rate' in locals() and not df_trades.empty:
        import numpy as np
        
        # --- 1. Cálculo de Riesgo de Ruina ---
        df_perdidas = df_trades[df_trades[col_beneficio] < 0]
        if not df_perdidas.empty:
            avg_loss_abs = abs(df_perdidas[col_beneficio].mean())
            limite_dd_dolares = balance_inicial * 0.10
            trades_para_ruina = int(limite_dd_dolares / avg_loss_abs) if avg_loss_abs > 0 else 999
            prob_perder = 1 - (win_rate / 100)
            prob_ruina_pct = (prob_perder ** trades_para_ruina) * 100
            
            color_ruina = "#00994d" if prob_ruina_pct < 0.1 else "#b8860b" if prob_ruina_pct < 1 else "#d93025"
            texto_ruina = "< 0.1%" if prob_ruina_pct < 0.1 else f"{prob_ruina_pct:.2f}%"
        else:
            trades_para_ruina, texto_ruina, color_ruina = 0, "0.00%", "#00994d"

        # --- 2. Cálculo Cuantitativo: Z-Score (Rachas) ---
        ganadores = (df_trades[col_beneficio] > 0).astype(int).values
        W = np.sum(ganadores == 1)
        L = np.sum(ganadores == 0)
        N = len(ganadores)
        
        if N > 1 and W > 0 and L > 0:
            R = 1 # Número de rachas (Runs)
            for i in range(1, N):
                if ganadores[i] != ganadores[i-1]:
                    R += 1
            mu_R = (2 * W * L / N) + 1
            std_R = np.sqrt((2 * W * L * (2 * W * L - N)) / ((N ** 2) * (N - 1)))
            z_score = (R - mu_R) / std_R if std_R > 0 else 0
        else:
            z_score = 0.0
            
        color_z = "#d93025" if z_score <= -2.0 else "#b8860b" if z_score < 0 else "#00994d"
        texto_z = "Tendencia a Rachas" if z_score < -1 else "Operativa Alterna" if z_score > 1 else "Aleatorio"

        # --- 3. Cálculo Cuantitativo: AHPR y GHPR ---
        retornos_pct = df_trades[col_beneficio] / balance_inicial
        ahpr = retornos_pct.mean() * 100
        multiplicadores = 1 + retornos_pct
        ghpr = (np.prod(multiplicadores) ** (1/len(multiplicadores)) - 1) * 100 if len(multiplicadores) > 0 else 0.0

        # --- RENDERIZADO DEL WIDGET TRIPLE (ESTILO NAVEGANTE) ---
        st.markdown(f"""
        <div style="display: flex; gap: 15px; margin-bottom: 25px; flex-wrap: wrap; position: relative; z-index: 1;">
            <div style="flex: 1; min-width: 200px; background-color: #0d1321; padding: 20px; border: 1px solid rgba(0,255,170,0.15); box-shadow: inset 0 0 20px rgba(0,255,170,0.02); border-radius: 4px;">
                <h4 style="margin:0; color: #00ffaa; font-family: 'JetBrains Mono', monospace; font-size: 13px; letter-spacing: 1.5px;">&#9678; RIESGO DE RUINA</h4>
                <span style="color: #5a6a7a; font-size: 10px; font-family: 'JetBrains Mono', monospace;">LÍMITE -10% CUENTA</span>
                <h2 style="margin:8px 0 0 0; color: {color_ruina}; font-size: 26px; font-family: 'JetBrains Mono', monospace;">{texto_ruina}</h2>
                <span style="color: #e0e6ed; font-size: 12px;"><b>{trades_para_ruina}</b> pérdidas seguidas</span>
            </div>
            <div style="flex: 1; min-width: 200px; background-color: #0d1321; padding: 20px; border: 1px solid rgba(0,255,170,0.15); box-shadow: inset 0 0 20px rgba(0,255,170,0.02); border-radius: 4px;">
                <h4 style="margin:0; color: #00d4ff; font-family: 'JetBrains Mono', monospace; font-size: 13px; letter-spacing: 1.5px;">&#9678; Z-SCORE (RACHAS)</h4>
                <span style="color: #5a6a7a; font-size: 10px; font-family: 'JetBrains Mono', monospace;">PATRÓN ESTADÍSTICO</span>
                <h2 style="margin:8px 0 0 0; color: {color_z}; font-size: 26px; font-family: 'JetBrains Mono', monospace;">{z_score:.2f}</h2>
                <span style="color: #e0e6ed; font-size: 12px;"><b>{texto_z}</b></span>
            </div>
            <div style="flex: 1; min-width: 200px; background-color: #0d1321; padding: 20px; border: 1px solid rgba(0,255,170,0.15); box-shadow: inset 0 0 20px rgba(0,255,170,0.02); border-radius: 4px;">
                <h4 style="margin:0; color: #ffaa00; font-family: 'JetBrains Mono', monospace; font-size: 13px; letter-spacing: 1.5px;">&#9678; CRECIMIENTO REAL</h4>
                <span style="color: #5a6a7a; font-size: 10px; font-family: 'JetBrains Mono', monospace;">GHPR POR OPERACIÓN</span>
                <h2 style="margin:8px 0 0 0; color: #00ffaa; font-size: 26px; font-family: 'JetBrains Mono', monospace;">{ghpr:.2f}%</h2>
                <span style="color: #e0e6ed; font-size: 12px;">AHPR: <b>{ahpr:.2f}%</b></span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 📊 Rendimiento Mensual")
    
    # El diccionario traductor que faltaba
    nombres_meses = {1: 'Ene', 2: 'Feb', 3: 'Mar', 4: 'Abr', 5: 'May', 6: 'Jun', 
                     7: 'Jul', 8: 'Ago', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dic'}
    
    # Preparamos los datos por mes
    df_meses = df_trades.groupby('Mes_Año_Sort')[col_beneficio].sum().reset_index()
    df_meses['Mes_Num'] = df_meses['Mes_Año_Sort'].dt.month
    df_meses['Año'] = df_meses['Mes_Año_Sort'].dt.year
    df_meses['Nombre_Mes'] = df_meses['Mes_Num'].map(nombres_meses)
    df_meses['Mes'] = df_meses['Nombre_Mes'] + " " + df_meses['Año'].astype(str)
    
    # Creamos la gráfica de barras
    if not df_meses.empty:
        fig_mes = go.Figure()
        
        # Magia: Calculamos el % basándonos en tu capital inicial
        if balance_inicial > 0:
            df_meses['Texto_Barra'] = df_meses.apply(
                lambda fila: f"${fila[col_beneficio]:,.2f}<br>({(fila[col_beneficio] / balance_inicial) * 100:+.2f}%)", 
                axis=1
            )
        else:
            df_meses['Texto_Barra'] = df_meses[col_beneficio].apply(lambda x: f"${x:,.2f}")

        # Colores: verde si ganas, rojo si pierdes
        colores_mes = ['#00cc66' if val >= 0 else '#ff4d4d' for val in df_meses[col_beneficio]]
        
        fig_mes.add_trace(go.Bar(
            x=df_meses['Mes'],
            y=df_meses[col_beneficio],
            marker_color=colores_mes,
            text=df_meses['Texto_Barra'],
            textposition='auto',
            textfont=dict(size=13, weight='bold')
        ))
        
        fig_mes.update_layout(
            height=350,
            margin=dict(l=0, r=0, t=30, b=0),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.2)', tickprefix='$')
        )
        
        # TRUCO DE DISEÑO: Lo metemos en la columna central
        col_izq, col_centro, col_der = st.columns([1, 4, 1])
        with col_centro:
            st.plotly_chart(fig_mes, use_container_width=True)
            
    else:
        st.info("No hay suficientes datos para mostrar el rendimiento mensual.")
    st.markdown("---")
    st.markdown("### 📅 Calendario Diario y Eventos")

    tab_pnl, tab_eco = st.tabs(["📊 PnL Operativo", "🌐 Calendario Económico"])

    with tab_pnl:
        meses_disponibles = df_trades['Mes_Año_Sort'].dt.strftime('%Y-%m').unique()
        if len(meses_disponibles) > 0:
            mes_seleccionado = st.selectbox("Selecciona el mes a visualizar:", meses_disponibles[::-1])
            year_sel, month_sel = map(int, mes_seleccionado.split('-'))
            df_mes_cal = df_trades[(df_trades['Año'] == year_sel) & (df_trades['Mes_Num'] == month_sel)]
            
            pnl_por_dia = df_mes_cal.groupby(df_mes_cal['Cierre'].dt.day).agg({col_beneficio: 'sum', 'Cuenta': 'count'}).to_dict('index')
            total_pnl_mes = df_mes_cal[col_beneficio].sum()
            total_ops_mes = df_mes_cal.shape[0]

            cal = calendar.HTMLCalendar(calendar.MONDAY)
            mes_dias = cal.monthdayscalendar(year_sel, month_sel)
            
            html_cal = """
            <style>
                .table-container { width: 100%; overflow-x: auto; margin-bottom: 10px; }
                .cal-table { width: 100%; border-collapse: collapse; font-family: 'JetBrains Mono', monospace; color: #e0e6ed; table-layout: fixed; border: 1px solid rgba(0,255,170,0.15); background-color: #0d1321; }
                @media screen and (max-width: 768px) {
                    .cal-table { min-width: 800px; }
                }
                .cal-th { background-color: rgba(0,255,170,0.05); padding: 10px; text-align: center; border: 1px solid rgba(0,255,170,0.15); font-size: 11px; text-transform: uppercase; font-weight: bold; color: #00ffaa; letter-spacing: 1px; }
                .cal-th-total { background-color: rgba(0,212,255,0.05); padding: 10px; text-align: center; border: 1px solid rgba(0,255,170,0.15); color: #00d4ff; white-space: nowrap; width: 120px; font-size: 11px; letter-spacing: 1px; }
                .cal-td { border: 1px solid rgba(0,255,170,0.1); height: 95px; vertical-align: top; padding: 6px; background-color: #0d1321; transition: 0.2s; }
                .cal-td:hover { background-color: rgba(0,255,170,0.02); }
                .cal-td-total { border: 1px solid rgba(0,255,170,0.15); height: 95px; vertical-align: middle; padding: 10px; background-color: rgba(0,255,170,0.02); font-size: 16px; font-weight: bold; text-align: center; white-space: nowrap; }
                .day-num { font-size: 12px; font-weight: bold; color: #5a6a7a; margin-bottom: 5px; border-bottom: 1px solid rgba(0,255,170,0.1); padding-bottom: 3px; }
                .profit { color: #00ffaa; font-weight: bold; text-align: center; margin-top: 5px; font-size: 15px; text-shadow: 0 0 5px rgba(0,255,170,0.3); }
                .loss { color: #ff3366; font-weight: bold; text-align: center; margin-top: 5px; font-size: 15px; text-shadow: 0 0 5px rgba(255,51,102,0.3); }
                .ops-count { color: #5a6a7a; text-align: center; margin-top: 3px; font-size: 10px; font-style: italic; }
                .neutral { color: #5a6a7a; text-align: center; margin-top: 10px; font-size: 13px; }
            </style>
            <div class="table-container">
                <table class="cal-table">
                    <tr><th class="cal-th">Lun</th><th class="cal-th">Mar</th><th class="cal-th">Mié</th><th class="cal-th">Jue</th><th class="cal-th">Vie</th><th class="cal-th">Sáb</th><th class="cal-th">Dom</th><th class="cal-th-total">TOTAL SEMANA</th></tr>
            """
            for semana in mes_dias:
                html_cal += "<tr>"
                suma_semana = 0
                for dia in semana:
                    if dia == 0:
                        # Fondo super oscuro para los días vacíos
                        html_cal += "<td class='cal-td' style='background-color: #0a0e17;'></td>"
                    else:
                        datos_dia = pnl_por_dia.get(dia, {col_beneficio: 0, 'Cuenta': 0})
                        resultado = datos_dia[col_beneficio]
                        num_ops = datos_dia['Cuenta']
                        suma_semana += resultado
                        
                        texto_ops = f"<div class='ops-count'>{num_ops} ops</div>" if num_ops > 0 else ""
                        
                        if resultado > 0: html_cal += f"<td class='cal-td'><div class='day-num'>{dia}</div><div class='profit'>+${resultado:,.2f}</div>{texto_ops}</td>"
                        elif resultado < 0: html_cal += f"<td class='cal-td'><div class='day-num'>{dia}</div><div class='loss'>-${abs(resultado):,.2f}</div>{texto_ops}</td>"
                        else: html_cal += f"<td class='cal-td'><div class='day-num'>{dia}</div><div class='neutral'>-</div></td>"
                
                color_total = '#00ffaa' if suma_semana > 0 else '#ff3366' if suma_semana < 0 else '#5a6a7a'
                signo = '+' if suma_semana > 0 else ''
                html_cal += f"<td class='cal-td-total' style='color: {color_total}'>{signo}${suma_semana:,.2f}</td>"
                html_cal += "</tr>"
            
            html_cal += """
                </table>
            </div>
            """
            st.markdown(html_cal, unsafe_allow_html=True)

            color_mes = "#00ffaa" if total_pnl_mes >= 0 else "#ff3366"
            signo_mes = "+" if total_pnl_mes >= 0 else ""
            html_mes = f"""
            <div style="background-color: #0d1321; padding: 15px; border-radius: 4px; border: 1px solid rgba(0,255,170,0.15); text-align: center; margin-top: 5px; box-shadow: inset 0 0 20px rgba(0,255,170,0.02);">
                <span style="color: #00d4ff; font-family: 'JetBrains Mono', monospace; font-size: 14px; font-weight: bold; text-transform: uppercase; letter-spacing: 1px;">Total {mes_seleccionado}:</span>
                <span style="color: {color_mes}; font-family: 'JetBrains Mono', monospace; font-size: 24px; font-weight: bold; margin-left: 15px; text-shadow: 0 0 8px {color_mes}40;">{signo_mes}${total_pnl_mes:,.2f}</span>
                <span style="color: #5a6a7a; font-family: 'JetBrains Mono', monospace; font-size: 12px; margin-left: 10px;">({total_ops_mes} operaciones)</span>
            </div>
            """
            st.markdown(html_mes, unsafe_allow_html=True)

    with tab_eco:
        components.html(
            """
            <div class="tradingview-widget-container">
              <div class="tradingview-widget-container__widget"></div>
              <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-events.js" async>
              {
              "colorTheme": "dark",
              "isTransparent": true,
              "width": "100%",
              "height": "450",
              "locale": "es",
              "importanceFilter": "-1,0,1",
              "currencyFilter": "USD,EUR,GBP,JPY,AUD,CAD,CHF,NZD"
              }
              </script>
            </div>
            """,
            height=450
        )

# === CIERRE DE SEGURIDAD DEL PANEL (NO BORRAR) ===
except Exception as e:
    st.error(f"Error cargando el panel: {e}")
    
    # ==========================================
    # 11. BITÁCORA Y DIARIO OPERATIVO
    # ==========================================
    st.markdown("---")
    st.markdown("### 📝 Diario Operativo (Bitácora)")
    st.write("Selecciona una fecha para leer o escribir tus notas y adjuntar capturas de pantalla de la sesión.")
    
    col_diario1, col_diario2 = st.columns([1, 1])
    
    with col_diario1:
        fecha_diario = st.date_input("📅 Fecha de la sesión:")
        fecha_str = fecha_diario.strftime("%Y-%m-%d")
        nota_path = f"Diario_Trading/nota_{fecha_str}.txt"
        img_path = f"Diario_Trading/Screenshots/img_{fecha_str}.png"
        
        nota_actual = ""
        if os.path.exists(nota_path):
            with open(nota_path, "r", encoding="utf-8") as f:
                nota_actual = f.read()
                
        nueva_nota = st.text_area(f"✍️ Tus impresiones del {fecha_str}:", value=nota_actual, height=180, placeholder="Ej: Hoy entré con buen setup, pero cerré antes de tiempo por miedo...")
        nueva_img = st.file_uploader("📸 Sube la captura de tus gráficos (opcional)", type=["png", "jpg", "jpeg"], key="img_uploader")
        
        if st.button("💾 Guardar Registro del Día"):
            with open(nota_path, "w", encoding="utf-8") as f:
                f.write(nueva_nota)
            if nueva_img is not None:
                with open(img_path, "wb") as f:
                    f.write(nueva_img.getbuffer())
            st.success("¡Registro guardado con éxito!")
            
    with col_diario2:
        if os.path.exists(img_path):
            st.markdown(f"**Captura guardada del {fecha_str}:**")
            st.image(img_path, use_container_width=True)
        else:
            st.info("No hay captura de pantalla guardada para este día.")

    st.markdown("---")

    # ==========================================
    # 12. HISTORIAL COMPLETO DE OPERACIONES
    # ==========================================
    st.markdown("### 🗃️ Historial Completo de Operaciones")
    
    df_history = df_trades[['Ticket', 'Fecha', 'Hora_Dia', col_simbolo, col_tipo, col_volumen, col_beneficio, 'Porcentaje_Trade']].copy()
    df_history.columns = ['Ticket', 'Fecha', 'Hora', 'Activo', 'Dirección', 'Lotes', 'Beneficio ($)', 'Crecimiento (%)']
    df_history = df_history.sort_values(by='Fecha', ascending=False)
    
    def color_texto(val):
        color = '#00e676' if val > 0 else '#ff4d4d' if val < 0 else '#888888'
        return f'color: {color}; font-weight: bold;'

    st.dataframe(
        df_history.style.map(color_texto, subset=['Beneficio ($)', 'Crecimiento (%)'])
        .format({'Beneficio ($)': '${:.2f}', 'Crecimiento (%)': '{:.2f}%'}), 
        use_container_width=True, 
        height=300
    )

    st.download_button(label="📥 Descargar Historial en Excel (CSV)", data=df_history.to_csv(index=False).encode('utf-8'), file_name='historial_operaciones.csv', mime='text/csv')

    # ==========================================
    # 13. INTERÉS COMPUESTO 
    # ==========================================
    st.markdown("---")
    st.markdown(f"### 🚀 Proyección de Interés Compuesto a {años_proyeccion} años")
    meses = años_proyeccion * 12
    capital_actual = df_trades['Equidad_Acumulada'].iloc[-1]
    
    datos_proyeccion = []
    cap_iterado = capital_actual
    for m in range(meses + 1):
        datos_proyeccion.append({'Mes': m, 'Capital': cap_iterado})
        cap_iterado *= (1 + objetivo_mensual / 100)
    
    df_proy = pd.DataFrame(datos_proyeccion)
    c_proy, c_info = st.columns([2, 1])
    
    with c_proy:
        fig_proy = px.area(df_proy, x='Mes', y='Capital', title=f"Crecimiento estimado al {objetivo_mensual}% mensual")
        fig_proy.update_traces(line_color='#00cc66', fillcolor='rgba(0, 204, 102, 0.2)')
        fig_proy.update_layout(template="plotly_dark")
        st.plotly_chart(fig_proy, use_container_width=True)
        
    with c_info:
        st.markdown("#### 🎯 Metas Financieras")
        final_cap = df_proy['Capital'].iloc[-1]
        st.write(f"**Capital Final:**")
        st.title(f"${final_cap:,.2f}")
        st.write(f"Multiplicador: **x{(final_cap/capital_actual):.1f}**")

except Exception as e:
    st.error(f"⚠️ ¡Vaya! Ha ocurrido un error: {e}")

# ==========================================
# SIMULADORES DE PROYECCIÓN Y RIESGO
# ==========================================
st.markdown("---")
st.markdown("### 🚀 Simuladores y Análisis de Riesgo")

tab_lineal, tab_montecarlo = st.tabs(["📈 Proyección Lineal", "🎲 Simulación Montecarlo"])

with tab_lineal:
    st.caption("Proyección matemática perfecta (Interés Compuesto).")
    col_sim1, col_sim2, col_sim3 = st.columns(3)
    with col_sim1:
        cap_inicial_sim = st.number_input("Capital Actual ($)", value=float(balance_inicial) if 'balance_inicial' in locals() and balance_inicial > 0 else 50000.0, step=1000.0, key="cap_lin")
    with col_sim2:
        obj_mensual_sim = st.number_input("Objetivo Mensual (%)", value=5.0, step=0.5)
    with col_sim3:
        meses_proy_sim = st.number_input("Meses a proyectar", value=12, step=1)

    meses_lista = list(range(1, int(meses_proy_sim) + 1))
    capital_proy = [cap_inicial_sim * (1 + (obj_mensual_sim/100))**m for m in meses_lista]

    fig_sim = go.Figure()
    fig_sim.add_trace(go.Scatter(
        x=[f"Mes {m}" for m in meses_lista], y=capital_proy,
        mode='lines+markers', line=dict(color='#00994d', width=3), marker=dict(size=8, color='#00994d')
    ))
    fig_sim.update_layout(
        height=300, margin=dict(l=0, r=0, t=30, b=0),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        yaxis=dict(tickprefix='$', showgrid=True, gridcolor='rgba(128,128,128,0.2)', tickfont=dict(color='#333')),
        xaxis=dict(showgrid=False, tickfont=dict(color='#333'))
    )
    st.plotly_chart(fig_sim, use_container_width=True)

with tab_montecarlo:
    st.caption("1,000 simulaciones basadas en tu historial real de operaciones para predecir Riesgo de Ruina.")
    
    # Extraemos tus trades reales del panel
    trades_reales = df_trades[col_beneficio].dropna().values
    
    if len(trades_reales) < 5:
        st.warning("⚠️ Necesitas registrar al menos 5 operaciones reales en el panel para que la simulación de Montecarlo tenga sentido estadístico.")
    else:
        import numpy as np
        
        col_mc1, col_mc2, col_mc3 = st.columns(3)
        with col_mc1:
            cap_inicial_mc = st.number_input("Capital Cuenta Fondeo ($)", value=float(balance_inicial) if 'balance_inicial' in locals() and balance_inicial > 0 else 50000.0, step=1000.0, key="cap_mc")
        with col_mc2:
            n_trades_sim = st.number_input("Operaciones a simular", value=100, step=10, key="ops_mc")
        with col_mc3:
            limite_perdida = st.number_input("Pérdida Máx. Permitida (%)", value=10.0, step=1.0, help="Ejemplo: FTMO no permite perder más del 10%.")

        # MAGIA MATEMÁTICA: 1000 simulaciones
        num_simulaciones = 1000
        simulaciones = np.random.choice(trades_reales, size=(num_simulaciones, int(n_trades_sim)), replace=True)
        curvas_capital = np.cumsum(simulaciones, axis=1) + cap_inicial_mc
        
        # Cálculos de Riesgo
        nivel_ruina = cap_inicial_mc * (1 - (limite_perdida / 100.0))
        simulaciones_arruinadas = np.any(curvas_capital <= nivel_ruina, axis=1)
        prob_ruina = (np.sum(simulaciones_arruinadas) / num_simulaciones) * 100
        
        # Gráfica Montecarlo
        fig_mc = go.Figure()
        
        # Pintamos solo 50 "realidades" para no saturar el ordenador
        for i in range(50):
            fig_mc.add_trace(go.Scatter(
                y=curvas_capital[i], mode='lines', 
                line=dict(color='rgba(100, 100, 100, 0.15)'), showlegend=False, hoverinfo='skip'
            ))
            
        # Pintamos la mediana (Lo más probable que ocurra)
        mediana_curva = np.median(curvas_capital, axis=0)
        fig_mc.add_trace(go.Scatter(
            y=mediana_curva, mode='lines', name='Curva Mediana Esperada',
            line=dict(color='#00994d', width=3)
        ))
        
        # Pintamos la línea de RUINA (El abismo de la cuenta fondeada)
        fig_mc.add_trace(go.Scatter(
            x=[0, int(n_trades_sim)-1], y=[nivel_ruina, nivel_ruina],
            mode='lines', name=f'Límite Ruina (-{limite_perdida}%)',
            line=dict(color='#d93025', width=2, dash='dash')
        ))
        
        fig_mc.update_layout(
            height=400, margin=dict(l=0, r=0, t=30, b=0),
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            yaxis=dict(tickprefix='$', showgrid=True, gridcolor='rgba(128,128,128,0.2)'),
            xaxis=dict(showgrid=False, title="Número de Operaciones Futuras"),
            showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        st.plotly_chart(fig_mc, use_container_width=True)
        
        # Veredicto de Riesgo
        color_ruina = "red" if prob_ruina > 5 else "orange" if prob_ruina > 1 else "green"
        st.markdown(f"### 🎲 Análisis de Resultados (1,000 Escenarios)")
        st.markdown(f"- **Probabilidad de perder la cuenta (Riesgo de Ruina):** :{color_ruina}[**{prob_ruina:.1f}%**] *(Ideal: < 1%)*")
        st.markdown(f"- **Capital esperado tras {int(n_trades_sim)} ops:** **${mediana_curva[-1]:,.2f}**")

# ==========================================
# 🤖 ASISTENTE DE TRADING IA (CEREBRO CUANTITATIVO)
# ==========================================
import google.generativeai as genai

st.markdown("---")
st.markdown("### 🧠 Tu Asistente de Trading Institucional")

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-2.5-flash')

    # --- 1. BOTÓN PARA LIMPIAR EL CHAT ---
    col1, col2 = st.columns([8, 2])
    with col2:
        if st.button("🗑️ Limpiar Chat"):
            st.session_state.mensajes_ia = []
            st.rerun()

# --- 2. EL SÚPER CONTEXTO INSTITUCIONAL (VERSIÓN QUANT) ---
    # 1. Variables de Riesgo y Cuantitativas
    z_score_val = z_score if 'z_score' in locals() else 0.0
    ghpr_val = ghpr if 'ghpr' in locals() else 0.0
    ahpr_val = ahpr if 'ahpr' in locals() else 0.0
    riesgo_ruina_str = f"{prob_ruina_pct:.4f}%" if 'prob_ruina_pct' in locals() else "Desconocido"
    trades_ruina_str = f"{trades_para_ruina}" if 'trades_para_ruina' in locals() else "Desconocido"
    perdida_media_str = f"${avg_loss_abs:,.2f}" if 'avg_loss_abs' in locals() else "Desconocido"

    # 2. Análisis de las operaciones de HOY en tiempo real
    hoy_fecha = pd.Timestamp.today().date()
    df_hoy = df_trades[df_trades['Cierre'].dt.date == hoy_fecha]
    
    if df_hoy.empty:
        resumen_hoy = "Hoy no has registrado ninguna operación. Día en blanco."
    else:
        ops_hoy = len(df_hoy)
        pnl_hoy = df_hoy[col_beneficio].sum()
        # Sacamos una lista con los resultados de hoy para que la IA vea si hay rachas
        lista_resultados = [f"${val:,.2f}" for val in df_hoy[col_beneficio].values]
        resumen_hoy = f"ATENCIÓN: Has realizado {ops_hoy} operaciones hoy. PnL Diario de hoy: ${pnl_hoy:,.2f}. Resultados individuales de hoy: {', '.join(lista_resultados)}."

    # 3. El Súper Prompt (El cerebro del CRO)
    contexto = f"""
    Eres el Director de Riesgos (Chief Risk Officer - CRO) de un fondo de inversión cuantitativo en Wall Street. 
    Estás analizando la cuenta de fondeo de tu trader principal. 
    PROHIBIDO decir que eres una IA, un modelo de lenguaje o que no tienes acceso a la cuenta. Estás conectado directamente por API a su terminal de MetaTrader y ves sus números en tiempo real.
    
    Tu tono debe ser analítico, directo, estrictamente profesional y sin rodeos. Eres constructivo pero implacable con la gestión de riesgo. No des consejos genéricos de libro, básate ÚNICA Y EXCLUSIVAMENTE en estas métricas exactas:

    📈 RENDIMIENTO GLOBAL Y VENTAJA ESTADÍSTICA (EDGE):
    - Win Rate: {win_rate:.1f}%
    - Profit Factor: {profit_factor:.2f}
    - Beneficio Neto Total: ${beneficio_total:,.2f}
    - GHPR (Crecimiento Real por trade): {ghpr_val:.4f}%
    - AHPR (Crecimiento Promedio): {ahpr_val:.4f}%
    - Z-Score (Patrón de Rachas): {z_score_val:.2f}
    
    🛡️ SUPERVIVENCIA ESTADÍSTICA (Límite Ruina -10%):
    - Probabilidad de Ruina Matemática: {riesgo_ruina_str}
    - Colchón de Supervivencia: Tienes margen para {trades_ruina_str} pérdidas consecutivas antes de quemar la cuenta.
    - Pérdida Promedio por trade malo: {perdida_media_str}

    📅 OPERATIVA EN VIVO DE HOY ({hoy_fecha.strftime('%d/%m/%Y')}):
    - {resumen_hoy}

    REGLAS DE RESPUESTA DEL CRO:
    1. Z-SCORE CRÍTICO: Si el Z-Score es muy negativo (por debajo de -3.0, como un -7.43), advierte al trader que su sistema es ALTAMENTE dependiente de rachas. Si hoy tiene pérdidas, exígele que APAGUE LAS PANTALLAS porque la estadística dicta que vendrán más operaciones rojas seguidas.
    2. CRECIMIENTO GHPR: Si el GHPR es muy bajo (ej. 0.01%), dile que está en "modo supervivencia": no pierde la cuenta gracias a su buena gestión de riesgo, pero apenas avanza. Hazle ver que necesita mejorar su ratio Riesgo/Beneficio (cortar pérdidas antes o dejar correr ganancias).
    3. Si te pregunta por su día de hoy, analiza el 'PnL Diario' y los trades individuales.
    4. Ve directo al grano. Usa listas, negritas y datos numéricos en tus respuestas. Compórtate como un auténtico profesional de las finanzas cuantitativas.
    """

    if "mensajes_ia" not in st.session_state:
        st.session_state.mensajes_ia = []

    for msg in st.session_state.mensajes_ia:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Pregúntame sobre tu operativa..."):
        st.session_state.mensajes_ia.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                respuesta = model.generate_content(f"{contexto}\n\nPregunta de la trader: {prompt}").text
                st.markdown(respuesta)
                st.session_state.mensajes_ia.append({"role": "assistant", "content": respuesta})
            except Exception as e:
                st.error(f"⚠️ Error exacto de Google: {e}")
else:
    st.warning("⚠️ No has configurado la API Key en Streamlit Secrets.")
