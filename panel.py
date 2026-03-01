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
IDS_DRIVE = [
    "1NF17F0noOU2BudzSvPYNJWzKX88W1hNi", # Cuenta 1
    "1hvx5_P2mVo0QUj1d-UABawK6yoOMLHnw"  # Cuenta 2
]

st.set_page_config(page_title="Pro Trading Journal", layout="wide", initial_sidebar_state="expanded")
st.title("📊 Panel Cuantitativo Multi-Cuenta Institucional")

# Función para descargar todas las cuentas y fusionarlas (Actualiza cada 10 min)
@st.cache_data(ttl=600) 
def cargar_datos_automaticos():
    lista_dfs = []
    for id_doc in IDS_DRIVE:
        url = f'https://drive.google.com/uc?id={id_doc}'
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

    df[col_beneficio] = pd.to_numeric(df[col_beneficio], errors='coerce')
    df = df.dropna(subset=[col_beneficio])

    # --- 🛠️ TRADUCTOR DEL HISTORIAL MANUAL (MYFXBOOK) ---
    # 1. Unificamos las columnas ANTES de crear el menú para que el panel lo detecte
    if 'Beneficio (USD)' in df.columns:
        df[col_beneficio] = df[col_beneficio].fillna(pd.to_numeric(df['Beneficio (USD)'], errors='coerce'))
        # Bautizamos estas operaciones para que salgan con nombre en el menú
        if 'Cuenta' not in df.columns:
            df['Cuenta'] = None
        df['Cuenta'] = df['Cuenta'].fillna('Historial_2_Años')
        
    if 'Acción' in df.columns:
        df[col_tipo] = df[col_tipo].fillna(df['Acción'])
        
    if 'Símbolo' in df.columns:
        df[col_simbolo] = df[col_simbolo].fillna(df['Símbolo'])
        
    if 'Fecha de cierre' in df.columns:
        df[col_fecha] = df[col_fecha].fillna(df['Fecha de cierre'])

    # Traducimos Comprar/Vender al idioma interno de tu panel (buy/sell)
    if col_tipo in df.columns:
        df[col_tipo] = df[col_tipo].astype(str).str.lower().replace({
            'comprar': 'buy', 'vender': 'sell', 'buy': 'buy', 'sell': 'sell'
        })
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

    st.sidebar.markdown("---")
    balance_inicial = st.sidebar.number_input("💰 Capital Inicial ($)", value=float(balance_detectado))
    
    st.sidebar.markdown("### 🏦 Flujo de Capital y Costes")
    retiros_acumulados = abs(depositos_df[depositos_df[col_beneficio] < 0][col_beneficio].sum())
    coste_pruebas = st.sidebar.number_input("💸 Coste de Pruebas de Fondeo ($)", min_value=0.0, value=0.0, step=50.0)
    
    beneficio_neto_real = retiros_acumulados - coste_pruebas
    
    st.sidebar.write(f"**Retiros Brutos:** ${retiros_acumulados:,.2f}")
    if beneficio_neto_real >= 0:
        st.sidebar.success(f"**Ganancia Neta (Bolsillo):** ${beneficio_neto_real:,.2f}")
    else:
        st.sidebar.error(f"**Pérdida Neta (Bolsillo):** ${beneficio_neto_real:,.2f}")

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
    df_trades = df[(df[col_simbolo].notna()) & (df[col_tipo].astype(str).str.lower() != 'balance')].copy()
    
    # Filtramos operaciones a cero (Entradas de MT5)
    df_trades = df_trades[df_trades[col_beneficio] != 0]

    if df_trades.empty:
        st.info("Aún no hay operaciones reales registradas.")
        st.stop()

    df_trades['Equidad_Acumulada'] = balance_inicial + df_trades[col_beneficio].cumsum()
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

    col_res1, col_res2, col_res3 = st.columns(3)
    col_res1.metric(f"Esta Semana", f"${pnl_semana:,.2f}", f"{pct_semana:,.2f}%")
    col_res2.metric(f"Este Mes", f"${pnl_mes:,.2f}", f"{pct_mes:,.2f}%")
    col_res3.metric(f"Este Año", f"${pnl_año:,.2f}", f"{pct_año:,.2f}%")

    st.markdown("---")
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    kpi1.metric("Beneficio Neto (Trading)", f"${beneficio_total:,.2f}")
    kpi2.metric("Win Rate Total", f"{win_rate:.1f}%")
    kpi3.metric("Profit Factor", f"{profit_factor:.2f}")
    kpi4.metric("Max Drawdown", f"-${max_drawdown_dinero:,.2f}", f"-{max_drawdown_pct:.2f}%", delta_color="inverse")
    kpi5.metric("Total Trades", f"{total_trades}")

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

    with col_mes:
        st.markdown("### 📊 Rendimiento Mensual (%)")
        df_mensual = df_trades.groupby('Mes_Año_Sort').agg(Beneficio_Total=(col_beneficio, 'sum'), Equidad_Final=('Equidad_Acumulada', 'last')).reset_index()
        df_mensual['Equidad_Inicial'] = df_mensual['Equidad_Final'].shift(1).fillna(balance_inicial)
        df_mensual['Crecimiento_Pct'] = (df_mensual['Beneficio_Total'] / df_mensual['Equidad_Inicial']) * 100
        df_mensual['Periodo'] = df_mensual['Mes_Año_Sort'].dt.strftime('%b %Y')
        df_mensual['Color'] = df_mensual['Crecimiento_Pct'].apply(lambda x: '#00cc66' if x > 0 else '#ff4d4d')

        fig_mensual = go.Figure(data=[go.Bar(
            x=df_mensual['Periodo'], y=df_mensual['Crecimiento_Pct'], marker_color=df_mensual['Color'],
            text=df_mensual['Crecimiento_Pct'].apply(lambda x: f"{x:,.2f}%"), textposition='outside'
        )])
        fig_mensual.update_layout(template="plotly_dark", margin=dict(l=0, r=0, t=30, b=0), yaxis_title="Crecimiento (%)")
        st.plotly_chart(fig_mensual, use_container_width=True)

    with col_cal:
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
                
                html_cal = f"""
                <style>
                    .cal-table {{ width: 100%; border-collapse: collapse; font-family: sans-serif; color: #eee; table-layout: fixed; margin-bottom: 10px; border: 2px solid #444; }}
                    .cal-th {{ background-color: #1e1e1e; padding: 10px; text-align: center; border: 1px solid #444; font-size: 13px; text-transform: uppercase; }}
                    .cal-th-total {{ background-color: #2b1d00; padding: 10px; text-align: center; border: 1px solid #444; color: #ffd700; white-space: nowrap; width: 120px; }}
                    .cal-td {{ border: 1px solid #444; height: 95px; vertical-align: top; padding: 6px; background-color: #0e1117; transition: 0.2s; }}
                    .cal-td-total {{ border: 1px solid #444; height: 95px; vertical-align: middle; padding: 10px; background-color: #1a1500; font-size: 16px; font-weight: bold; text-align: center; white-space: nowrap; }}
                    .day-num {{ font-size: 14px; font-weight: bold; color: #aaa; margin-bottom: 5px; border-bottom: 1px solid #333; padding-bottom: 3px; }}
                    .profit {{ color: #00cc66; font-weight: bold; text-align: center; margin-top: 5px; font-size: 15px; }}
                    .loss {{ color: #ff4d4d; font-weight: bold; text-align: center; margin-top: 5px; font-size: 15px; }}
                    .ops-count {{ color: #b3b3b3; text-align: center; margin-top: 3px; font-size: 12px; font-style: italic; }}
                    .neutral {{ color: #888; text-align: center; margin-top: 10px; font-size: 13px; }}
                </style>
                <table class="cal-table">
                    <tr><th class="cal-th">Lun</th><th class="cal-th">Mar</th><th class="cal-th">Mié</th><th class="cal-th">Jue</th><th class="cal-th">Vie</th><th class="cal-th">Sáb</th><th class="cal-th">Dom</th><th class="cal-th-total">TOTAL SEMANA</th></tr>
                """
                for semana in mes_dias:
                    html_cal += "<tr>"
                    suma_semana = 0
                    for dia in semana:
                        if dia == 0:
                            html_cal += "<td class='cal-td' style='background-color: #050505;'></td>"
                        else:
                            datos_dia = pnl_por_dia.get(dia, {col_beneficio: 0, 'Cuenta': 0})
                            resultado = datos_dia[col_beneficio]
                            num_ops = datos_dia['Cuenta']
                            suma_semana += resultado
                            
                            texto_ops = f"<div class='ops-count'>{num_ops} ops</div>" if num_ops > 0 else ""
                            
                            if resultado > 0: html_cal += f"<td class='cal-td'><div class='day-num'>{dia}</div><div class='profit'>+${resultado:,.2f}</div>{texto_ops}</td>"
                            elif resultado < 0: html_cal += f"<td class='cal-td'><div class='day-num'>{dia}</div><div class='loss'>-${abs(resultado):,.2f}</div>{texto_ops}</td>"
                            else: html_cal += f"<td class='cal-td'><div class='day-num'>{dia}</div><div class='neutral'>-</div></td>"
                    
                    color_total = '#00cc66' if suma_semana > 0 else '#ff4d4d' if suma_semana < 0 else '#888'
                    signo = '+' if suma_semana > 0 else ''
                    html_cal += f"<td class='cal-td-total' style='color: {color_total}'>{signo}${suma_semana:,.2f}</td>"
                    html_cal += "</tr>"
                html_cal += "</table>"
                st.markdown(html_cal, unsafe_allow_html=True)

                color_mes = "#00cc66" if total_pnl_mes >= 0 else "#ff4d4d"
                signo_mes = "+" if total_pnl_mes >= 0 else ""
                html_mes = f"""
                <div style="background-color: #1e1e1e; padding: 15px; border-radius: 6px; border: 1px solid #444; text-align: center; margin-top: 5px;">
                    <span style="color: #eee; font-size: 16px; font-weight: bold; text-transform: uppercase;">Total {mes_seleccionado}:</span>
                    <span style="color: {color_mes}; font-size: 24px; font-weight: bold; margin-left: 15px;">{signo_mes}${total_pnl_mes:,.2f}</span>
                    <span style="color: #aaa; font-size: 14px; margin-left: 10px;">({total_ops_mes} operaciones)</span>
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

    # --- 2. EL SÚPER CONTEXTO INSTITUCIONAL ---
    contexto = f"""
    Eres un Gestor de Riesgos Cuantitativo Institucional. Estás CONECTADO DIRECTAMENTE a mi panel de trading y tienes ACCESO TOTAL a mis datos en tiempo real.
    PROHIBIDO decir que no tienes acceso a mi información o que eres solo una IA. 
    
    Mis métricas EXACTAS ACTUALIZADAS en este milisegundo son:
    - Win Rate: {win_rate:.1f}%
    - Profit Factor: {profit_factor:.2f}
    - Beneficio Neto: ${beneficio_total:,.2f}
    
    Usa estos datos exactos para responder. Sé directo, profesional, analítico y no uses advertencias genéricas.
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
