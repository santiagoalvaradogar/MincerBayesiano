import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from io import BytesIO
import json
import numpy as np

# ============================================
# CONFIGURACIÓN DE LA PÁGINA
# ============================================
st.set_page_config(
    page_title="Monitor Laboral México",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Monitor del Mercado Laboral Mexicano")
st.markdown("### Análisis de desigualdad y retornos a la educación (2007-2024)")

# ============================================
# ENLACES PÚBLICOS DE GOOGLE DRIVE
# ============================================
URLS = {
    "bayes": "https://drive.google.com/uc?export=download&id=1VX4T-HqiWXSLisdkz3fKPq1tu-KUKWYc",
    "mincer_ols": "https://drive.google.com/uc?export=download&id=1JTzqb021uiHQR6j7GEPL2j0At4cPP58b",
    "mincer_quantile": "https://drive.google.com/uc?export=download&id=1Blu9wxy6E8SBzew9EUuvCRIK_14j4Wnk",
    "gini_theil": "https://drive.google.com/uc?export=download&id=1IDrC-VojrjWOAMaerOGQMSiffvy0jBWh",
    "oaxaca": "https://drive.google.com/uc?export=download&id=1Kgieov10yhCH6D4qoHSqU8DuhaQCFX7a",
    "informalidad": "https://drive.google.com/uc?export=download&id=1c-AHqzJEI3B61RdJ0dPGkpoKwp9wZbYR",
    # ✅ Enlace correcto
    "resumen_estado": "https://drive.google.com/uc?export=download&id=1EsbPoLoDo9fnlg1BU6CvM1a3pjJen4Fi",
    "geojson_mexico": "https://drive.google.com/uc?export=download&id=15SUfCVqv8R4yO7rdfJ5hidmosuLWKPhV",
    "distribucion_seguridad": "https://drive.google.com/uc?export=download&id=1AJ6JYxeFjUdVvEl2uo69qZaYcBTlDLgq",
    "metricas_sectoriales": "https://drive.google.com/uc?export=download&id=14XgdFCUjldBr70918scHGy3n64EYx68r",
    "beta_mincer_estado": "https://drive.google.com/uc?export=download&id=1dSlx8dxcfRiu9v2NlxjWjKCd3cQi4qCa",
    # Si no usas oaxaca_estado, coméntalo o elimínalo:
    "oaxaca_estado": "https://drive.google.com/uc?export=download&id=1VakZMzmukDxEjIVnRM0BjaydFMiDBq5a",
}

# ============================================
# MAPEO DE CÓDIGOS INEGI → CÓDIGOS GEOJSON
# ============================================
CODES_MAP = {
    "01": "MX-AGU", "02": "MX-BCN", "03": "MX-BCS", "04": "MX-CAM",
    "05": "MX-COA", "06": "MX-COL", "07": "MX-CHP", "08": "MX-CHH",
    "09": "MX-CMX", "10": "MX-DUR", "11": "MX-GUA", "12": "MX-GRO",
    "13": "MX-HID", "14": "MX-JAL", "15": "MX-MEX", "16": "MX-MIC",
    "17": "MX-MOR", "18": "MX-NAY", "19": "MX-NLE", "20": "MX-OAX",
    "21": "MX-PUE", "22": "MX-QUE", "23": "MX-ROO", "24": "MX-SLP",
    "25": "MX-SIN", "26": "MX-SON", "27": "MX-TAB", "28": "MX-TAM",
    "29": "MX-TLA", "30": "MX-VER", "31": "MX-YUC", "32": "MX-ZAC",
}

# ============================================
# MAPEO DE CÓDIGOS SCIAN → NOMBRE DE SECTOR
# ============================================
SCIAN_MAP = {
    1: "Agropecuario", 2: "Minería", 3: "Energía", 4: "Construcción",
    5: "Manufacturas", 6: "Comercio mayorista", 7: "Comercio minorista",
    8: "Transporte", 9: "Medios", 10: "Finanzas", 11: "Inmobiliario",
    12: "Prof./Cient./Téc.", 13: "Corporativos", 14: "Apoyo a negocios",
    15: "Educación", 16: "Salud", 17: "Cultura/Deporte",
    18: "Hospedaje/Alim.", 19: "Otros serv.", 20: "Gobierno"
}

# ============================================
# FUNCIONES DE CARGA
# ============================================
@st.cache_data(ttl=3600)
def cargar_csv(url):
    """Carga un CSV desde una URL, detectando delimitador automáticamente."""
    try:
        response = requests.get(url, timeout=60)
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            # Detectar delimitador: si hay más pipes que comas, usar pipe
            if content.count('|') > content.count(','):
                return pd.read_csv(BytesIO(response.content), delimiter='|', encoding='utf-8')
            else:
                return pd.read_csv(BytesIO(response.content), encoding='utf-8')
        return None
    except Exception as e:
        st.warning(f"No se pudo cargar: {url}")
        return None
    
@st.cache_data(ttl=3600)
def cargar_desde_local(archivo):
    """Carga un CSV desde el sistema local."""
    try:
        df = pd.read_csv(f"resultados/{archivo}")
        if not df.empty:
            return df
        return None
    except:
        return None

@st.cache_data(ttl=3600)
def cargar_geojson(url):
    """Carga un GeoJSON desde una URL."""
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.warning(f"No se pudo cargar el GeoJSON: {e}")
        return None

# ============================================
# CARGA DE DATOS
# ============================================
with st.spinner("Cargando datos desde Google Drive..."):
    bayes = cargar_csv(URLS["bayes"])
    if bayes is None:
        bayes = cargar_desde_local("bayes_por_anio.csv")
    
    mincer_ols = cargar_csv(URLS["mincer_ols"])
    if mincer_ols is None:
        mincer_ols = cargar_desde_local("mincer_ols_por_anio.csv")
    
    mincer_quantile = cargar_csv(URLS["mincer_quantile"])
    if mincer_quantile is None:
        mincer_quantile = cargar_desde_local("mincer_quantile_por_anio.csv")
    
    gini_theil = cargar_csv(URLS["gini_theil"])
    if gini_theil is None:
        gini_theil = cargar_desde_local("gini_theil_por_anio.csv")
    
    oaxaca = cargar_csv(URLS["oaxaca"])
    if oaxaca is None:
        oaxaca = cargar_desde_local("oaxaca_blinder_por_anio.csv")
    
    informalidad = cargar_csv(URLS["informalidad"])
    if informalidad is None:
        informalidad = cargar_desde_local("modelo_informalidad.csv")
        
    dist_seguridad = cargar_csv(URLS["distribucion_seguridad"])
    if dist_seguridad is None:
        dist_seguridad = cargar_desde_local("distribucion_seguridad.csv")
        
    metricas_sect = cargar_csv(URLS["metricas_sectoriales"])
    if metricas_sect is None:
        metricas_sect = cargar_desde_local("metricas_sectoriales.csv")
    
    resumen_estado = cargar_csv(URLS["resumen_estado"])
    if resumen_estado is None:
        resumen_estado = cargar_desde_local("resumen_estado_anio.csv")
    
    geojson = cargar_geojson(URLS["geojson_mexico"])

# ============================================
# SIDEBAR - FILTROS
# ============================================
st.sidebar.header("🎛️ Filtros")

anios = []
if resumen_estado is not None and "year" in resumen_estado.columns:
    anios = sorted(resumen_estado["year"].unique())
elif bayes is not None and "year" in bayes.columns:
    anios = sorted(bayes["year"].unique())
else:
    anios = [2007, 2014, 2021, 2024]

anio_seleccionado = st.sidebar.selectbox("Selecciona un año", anios)

metricas_mapa = {
    "salario_promedio": "Salario promedio por hora (pesos)",
    "lnw_promedio": "Logaritmo del salario promedio",
    "educacion_promedio": "Años de educación promedio",
    "formalidad": "Tasa de formalidad"
}

metrica_seleccionada = st.sidebar.selectbox(
    "Métrica para el mapa",
    options=list(metricas_mapa.keys()),
    format_func=lambda x: metricas_mapa[x]
)

st.sidebar.markdown("---")
st.sidebar.markdown("**Datos:** ENOE-INEGI")
st.sidebar.markdown("**Modelos:** Mincer, Bayesiano, Oaxaca-Blinder")
st.sidebar.markdown("**Última actualización:** 2024")

# ============================================
# DIAGNÓSTICO PARA DEPURAR EL MAPA
# ============================================
if resumen_estado is not None and geojson is not None:
    st.sidebar.markdown("---")
    st.sidebar.markdown("**🔍 Diagnóstico del mapa**")
    
    codigos_datos = resumen_estado["ent"].astype(str).str.zfill(2).unique()[:5]
    st.sidebar.write(f"Códigos en datos (muestra): {list(codigos_datos)}")
    
    if "features" in geojson and len(geojson["features"]) > 0:
        feature = geojson["features"][0]
        if "id" in feature:
            codigo_ejemplo = feature["id"]
            st.sidebar.write(f"Código en GeoJSON (ejemplo): {codigo_ejemplo}")
        elif "properties" in feature and "CVE_ENT" in feature["properties"]:
            codigo_ejemplo = feature["properties"]["CVE_ENT"]
            st.sidebar.write(f"Código en GeoJSON (ejemplo): {codigo_ejemplo}")

# ============================================
# PESTAÑAS PRINCIPALES
# ============================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Retornos a la Educación",
    "🗺️ Desigualdad Regional",
    "⚖️ Brecha de Género",
    "📊 Probabilidad País",
    "🏭 Análisis Sectorial"
])

# ============================================
# TAB 1: RETORNOS A LA EDUCACIÓN
# ============================================
with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Evolución de β de Mincer (OLS)")
        if mincer_ols is not None and not mincer_ols.empty:
            fig = px.line(
                mincer_ols,
                x="year",
                y=["beta_esc", "beta_exp", "beta_female", "beta_formal"],
                title="Coeficientes de Mincer (OLS)",
                labels={"value": "Coeficiente", "year": "Año", "variable": "Variable"}
            )
            st.plotly_chart(fig, width='stretch')
        else:
            st.info("Datos de Mincer OLS no disponibles")
    
    with col2:
        st.subheader(f"Parámetros Bayesianos - {anio_seleccionado}")
        if bayes is not None and not bayes.empty:
            if "year" in bayes.columns:
                df_anio = bayes[bayes["year"] == anio_seleccionado]
            else:
                df_anio = bayes
            
            if not df_anio.empty:
                fig = px.bar(
                    df_anio,
                    x="param",
                    y="mean",
                    error_y="sd",
                    title=f"Modelo Bayesiano Mincer ({anio_seleccionado})",
                    labels={"mean": "Estimación", "param": "Parámetro"}
                )
                st.plotly_chart(fig, width='stretch')
                
                with st.expander("Ver tabla de parámetros"):
                    st.dataframe(df_anio)
            else:
                st.info(f"No hay datos bayesianos para {anio_seleccionado}")
        else:
            st.info("Datos bayesianos no disponibles")
    
    st.subheader("Retornos a la Escolaridad por Cuantil")
    if mincer_quantile is not None and not mincer_quantile.empty:
        fig = px.line(
            mincer_quantile,
            x="year",
            y="beta_esc",
            color="quantile",
            title="Retorno a la educación por cuantil de ingreso",
            labels={"beta_esc": "β de escolaridad", "year": "Año"}
        )
        st.plotly_chart(fig, width='stretch')
    else:
        st.info("Datos de quantile regression no disponibles")

# ============================================
# TAB 2: DESIGUALDAD REGIONAL (CON MAPA DE BETA Y FORMALIDAD CORREGIDA)
# ============================================
with tab2:
    st.subheader("🗺️ Desigualdad y Retornos Educativos por Estado")
    
    # Cargar archivos necesarios
    resumen_estado = cargar_csv(URLS.get("resumen_estado", ""))
    if resumen_estado is None:
        resumen_estado = cargar_desde_local("resumen_estado_anio.csv")
    
    beta_estado = cargar_csv(URLS.get("beta_mincer_estado", ""))
    if beta_estado is None:
        beta_estado = cargar_desde_local("beta_mincer_estado_anio.csv")
    
    geojson = cargar_geojson(URLS["geojson_mexico"])
    
    # ============================================
    # FUNCIÓN PARA NORMALIZAR ENTIDADES
    # ============================================
    def normalizar_entidad(df):
        if df is None or df.empty:
            return None, None
        candidatos = ['ent', 'CVE_ENT', 'cve_ent', 'ent_str', 'ENT', 'ENTIDAD', 'estado', 'ESTADO']
        col_ent = None
        for col in df.columns:
            if col in candidatos:
                col_ent = col
                break
        if col_ent is None:
            for col in df.columns:
                if 'ent' in col.lower() or 'cve' in col.lower() or 'estado' in col.lower():
                    col_ent = col
                    break
        if col_ent is None:
            return None, None
        df_norm = df.copy()
        df_norm['ent_str'] = df_norm[col_ent].astype(str).str.zfill(2)
        df_norm['codigo_geo'] = df_norm['ent_str'].map(CODES_MAP)
        return df_norm, col_ent
    
    # ============================================
    # DETECTAR AÑOS DISPONIBLES
    # ============================================
    years_available = []
    if resumen_estado is not None and not resumen_estado.empty:
        years_available = sorted(resumen_estado["year"].unique())
    elif beta_estado is not None and not beta_estado.empty:
        years_available = sorted(beta_estado["year"].unique())
    else:
        years_available = [2007, 2014, 2021, 2024]
    
    if not years_available:
        st.error("❌ No se encontraron datos para ningún año.")
        st.stop()
    
    anio_mapa = st.selectbox("Selecciona un año", years_available, key="anio_mapa_tab2")
    
    # ============================================
    # SELECTOR DE MÉTRICA
    # ============================================
    opciones_mapa = {
        "salario_promedio": "Salario promedio por hora (pesos)",
        "lnw_promedio": "Logaritmo del salario promedio",
        "educacion_promedio": "Años de educación promedio",
        "formalidad": "Tasa de formalidad (%)",
        "beta_esc": "Retorno a la educación (β de Mincer)"
    }
    
    metrica_mapa = st.selectbox(
        "Selecciona una métrica para el mapa",
        options=list(opciones_mapa.keys()),
        format_func=lambda x: opciones_mapa[x]
    )
    
    # ============================================
    # PREPARAR DATOS SEGÚN MÉTRICA (CORREGIDO)
    # ============================================
    df_mapa = None
    
    if metrica_mapa == "beta_esc":
        if beta_estado is not None and not beta_estado.empty:
            df_temp = beta_estado[beta_estado["year"] == anio_mapa].copy()
            if not df_temp.empty:
                df_temp, col_ent = normalizar_entidad(df_temp)
                if df_temp is not None:
                    # Verificar que la columna existe
                    if "beta_esc" in df_temp.columns:
                        df_temp["valor"] = df_temp["beta_esc"]
                    else:
                        st.error("❌ Columna 'beta_esc' no encontrada")
                        df_temp = None
                    df_mapa = df_temp
        else:
            st.warning("⚠️ Datos de beta Mincer por estado no disponibles")
    else:
        # Para salario, educación, formalidad
        if resumen_estado is not None and not resumen_estado.empty:
            df_temp = resumen_estado[resumen_estado["year"] == anio_mapa].copy()
            if not df_temp.empty:
                df_temp, col_ent = normalizar_entidad(df_temp)
                if df_temp is not None:
                    # 🔥 VERIFICAR QUE LA COLUMNA EXISTA ANTES DE RENOMBRAR
                    if metrica_mapa in df_temp.columns:
                        df_temp["valor"] = df_temp[metrica_mapa]
                    else:
                        st.error(f"❌ Columna '{metrica_mapa}' no encontrada. Columnas disponibles: {df_temp.columns.tolist()}")
                        df_temp = None
                    df_mapa = df_temp
        else:
            st.warning("⚠️ Datos de resumen_estado no disponibles")
    
    # ============================================
    # MOSTRAR MAPA (con diagnóstico)
    # ============================================
    if df_mapa is not None and not df_mapa.empty:
        # Eliminar filas sin valor
        df_mapa = df_mapa[df_mapa["valor"].notna()]
        df_mapa = df_mapa[df_mapa["codigo_geo"].notna()]
        
        if not df_mapa.empty and geojson is not None:
            # 🔥 MOSTRAR DIAGNÓSTICO DE FORMALIDAD
            if metrica_mapa == "formalidad":
                st.info(f"📊 Valores de formalidad: min={df_mapa['valor'].min():.3f}, max={df_mapa['valor'].max():.3f}, mean={df_mapa['valor'].mean():.3f}")
            
            st.info(f"✅ {len(df_mapa)} estados mapeados correctamente")
            
            # Escala de colores
            if metrica_mapa == "beta_esc":
                color_scale = "RdYlBu_r"
            elif metrica_mapa == "formalidad":
                color_scale = "YlGnBu"
            else:
                color_scale = "Viridis"
            
            # Rango de colores
            vmin = df_mapa["valor"].quantile(0.05)
            vmax = df_mapa["valor"].quantile(0.95)
            
            fig = px.choropleth(
                df_mapa,
                geojson=geojson,
                locations="codigo_geo",
                featureidkey="id",
                color="valor",
                color_continuous_scale=color_scale,
                range_color=(vmin, vmax) if not np.isnan(vmin) else None,
                labels={"valor": opciones_mapa[metrica_mapa]},
                title=f"{opciones_mapa[metrica_mapa]} por estado ({anio_mapa})"
            )
            
            fig.update_geos(fitbounds="locations", visible=False)
            fig.update_layout(margin={"r":0, "t":30, "l":0, "b":0})
            st.plotly_chart(fig, width='stretch')
            
            with st.expander("📋 Ver datos por estado"):
                # Mostrar columnas relevantes
                cols_mostrar = ["ent_str", "codigo_geo", "valor"]
                if metrica_mapa == "formalidad":
                    # Mostrar también el valor en porcentaje
                    df_show = df_mapa.copy()
                    df_show["formalidad_%"] = df_show["valor"] * 100
                    st.dataframe(df_show[["ent_str", "formalidad_%"]])
                else:
                    st.dataframe(df_mapa[cols_mostrar])
        else:
            if geojson is None:
                st.error("❌ No se pudo cargar el GeoJSON.")
            else:
                st.warning("⚠️ No hay datos con código GeoJSON válido para mostrar.")
    else:
        st.warning(f"⚠️ No hay datos disponibles para {anio_mapa} con la métrica seleccionada")
    
    # ============================================
    # GRÁFICOS NACIONALES DE GINI Y THEIL
    # ============================================
    st.subheader("📊 Evolución de la Desigualdad Nacional (Gini y Theil)")
    col1, col2 = st.columns(2)
    
    with col1:
        if gini_theil is not None and not gini_theil.empty:
            fig = px.line(
                gini_theil,
                x="year",
                y=["gini", "theil"],
                title="Evolución del Gini y Theil",
                labels={"value": "Índice", "year": "Año", "variable": "Medida"}
            )
            st.plotly_chart(fig, width='stretch')
        else:
            st.info("Datos de Gini/Theil no disponibles")
    
    with col2:
        if gini_theil is not None and not gini_theil.empty:
            fig = px.bar(
                gini_theil,
                x="year",
                y="gini",
                title="Coeficiente de Gini por Año",
                labels={"gini": "Gini", "year": "Año"},
                color="gini",
                color_continuous_scale="RdBu_r"
            )
            st.plotly_chart(fig, width='stretch')
        else:
            st.info("Datos de Gini no disponibles")
    
    with st.expander("ℹ️ ¿Qué miden estos indicadores?"):
        st.markdown("""
        - **Gini**: Mide la desigualdad en la distribución del ingreso (0 = perfecta igualdad, 1 = máxima desigualdad).
        - **Theil**: Otro índice de desigualdad que permite descomposición entre grupos.
        - **β de Mincer**: Retorno porcentual a un año adicional de educación (estimado por estado).
        - **Mapa**: Visualización geográfica de las métricas seleccionadas por estado.
        """)
        
# ============================================
# TAB 3: BRECHA DE GÉNERO (SOLO OAXACA)
# ============================================
with tab3:
    st.subheader("⚖️ Brecha de Género y Mapa Estatal")
    
    # Cargar archivos
    oaxaca_nacional = cargar_csv(URLS.get("oaxaca", ""))
    if oaxaca_nacional is None:
        oaxaca_nacional = cargar_desde_local("oaxaca_blinder_por_anio.csv")
    
    oaxaca_estado = cargar_csv(URLS.get("oaxaca_estado", ""))
    if oaxaca_estado is None:
        oaxaca_estado = cargar_desde_local("oaxaca_estado_anio.csv")
    
    geojson = cargar_geojson(URLS["geojson_mexico"])
    
    # ============================================
    # FUNCIÓN PARA NORMALIZAR ENTIDADES
    # ============================================
    def normalizar_entidad(df):
        if df is None or df.empty:
            return None, None
        candidatos = ['ent', 'CVE_ENT', 'cve_ent', 'ent_str', 'ENT', 'ENTIDAD', 'estado', 'ESTADO']
        col_ent = None
        for col in df.columns:
            if col in candidatos:
                col_ent = col
                break
        if col_ent is None:
            for col in df.columns:
                if 'ent' in col.lower() or 'cve' in col.lower() or 'estado' in col.lower():
                    col_ent = col
                    break
        if col_ent is None:
            return None, None
        df_norm = df.copy()
        df_norm['ent_str'] = df_norm[col_ent].astype(str).str.zfill(2)
        df_norm['codigo_geo'] = df_norm['ent_str'].map(CODES_MAP)
        return df_norm, col_ent
    
    # ============================================
    # AÑOS DISPONIBLES
    # ============================================
    years_available = []
    if oaxaca_estado is not None and not oaxaca_estado.empty:
        years_available = sorted(oaxaca_estado["year"].unique())
    elif oaxaca_nacional is not None and not oaxaca_nacional.empty:
        years_available = sorted(oaxaca_nacional["year"].unique())
    else:
        years_available = [2007, 2014, 2021, 2024]
    
    if not years_available:
        st.error("❌ No se encontraron datos para ningún año.")
        st.stop()
    
    anio_mapa = st.selectbox("Selecciona un año", years_available, key="anio_mapa_oaxaca")
    
    # ============================================
    # MAPA DE OAXACA POR ESTADO
    # ============================================
    st.subheader(f"🗺️ Brecha No Explicada (Oaxaca-Blinder) - {anio_mapa}")
    
    if oaxaca_estado is not None and not oaxaca_estado.empty:
        df_temp = oaxaca_estado[oaxaca_estado["year"] == anio_mapa].copy()
        if not df_temp.empty:
            df_temp, col_ent = normalizar_entidad(df_temp)
            if df_temp is not None:
                df_temp = df_temp.rename(columns={"unexplained": "valor"})
                df_mapa = df_temp[df_temp["valor"].notna()]
                df_mapa = df_mapa[df_mapa["codigo_geo"].notna()]
                
                if not df_mapa.empty and geojson is not None:
                    st.info(f"✅ {len(df_mapa)} estados mapeados correctamente")
                    
                    fig = px.choropleth(
                        df_mapa,
                        geojson=geojson,
                        locations="codigo_geo",
                        featureidkey="id",
                        color="valor",
                        color_continuous_scale="RdBu_r",
                        range_color=(df_mapa["valor"].quantile(0.05),
                                     df_mapa["valor"].quantile(0.95)),
                        labels={"valor": "Brecha no explicada (ln salario-hora)"},
                        title=f"Brecha no explicada por estado ({anio_mapa})"
                    )
                    fig.update_geos(fitbounds="locations", visible=False)
                    fig.update_layout(margin={"r":0, "t":30, "l":0, "b":0})
                    st.plotly_chart(fig, width='stretch')
                    
                    with st.expander("📋 Ver datos por estado"):
                        st.dataframe(df_mapa[["ent_str", "codigo_geo", "valor"]])
                else:
                    st.warning("No hay datos con código GeoJSON válido para mostrar.")
        else:
            st.warning(f"No hay datos de Oaxaca por estado para {anio_mapa}")
    else:
        st.warning("⚠️ No se encontró el archivo oaxaca_estado_anio.csv. Ejecuta el script para generarlo.")
    
    # ============================================
    # GRÁFICOS NACIONALES
    # ============================================
    st.subheader("📊 Evolución de la Brecha Salarial (Nacional)")
    
    if oaxaca_nacional is not None and not oaxaca_nacional.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.line(
                oaxaca_nacional,
                x="year",
                y=["gap", "explained", "unexplained"],
                title="Descomposición de la Brecha Salarial",
                labels={"value": "Diferencia en ln(salario)", "year": "Año", "variable": "Componente"}
            )
            st.plotly_chart(fig, width='stretch')
        
        with col2:
            fig = px.bar(
                oaxaca_nacional,
                x="year",
                y="unexplained",
                title="Brecha No Explicada (discriminación)",
                labels={"unexplained": "Brecha no explicada", "year": "Año"},
                color="unexplained",
                color_continuous_scale="RdBu_r"
            )
            st.plotly_chart(fig, width='stretch')
        
        with st.expander("📋 Ver tabla de Oaxaca-Blinder (nacional)"):
            st.dataframe(oaxaca_nacional)
    else:
        st.info("📊 Datos de Oaxaca-Blinder nacional no disponibles")
    
    st.markdown("""
    **Interpretación:**
    - **Brecha total**: Diferencia salarial promedio entre hombres y mujeres.
    - **Explicado**: Parte atribuible a diferencias en productividad (educación, experiencia, etc.).
    - **No explicado**: Parte atribuible a discriminación u otros factores no observables.
    """)
# ============================================

# TAB 4: PROBABILIDAD PAÍS (CORREGIDO - CON COEFICIENTES DE ESTADOS)
# ============================================
with tab4:
    st.subheader("Seguridad Social y Formalidad en México")
    
    col1, col2 = st.columns(2)
    
    # ======================
    # Columna 1: Distribución de seguridad social
    # ======================
    with col1:
        st.markdown("#### Distribución por tipo de institución")
        
        distribucion = cargar_csv(URLS.get("distribucion_seguridad", ""))
        if distribucion is None:
            distribucion = cargar_desde_local("distribucion_seguridad.csv")
        
        if distribucion is not None and not distribucion.empty:
            df_dist = distribucion[distribucion["year"] == anio_seleccionado]
            if not df_dist.empty:
                fig = px.bar(
                    df_dist,
                    x="seguridad_cat",
                    y="porcentaje",
                    title=f"Distribución de seguridad social ({anio_seleccionado})",
                    labels={"seguridad_cat": "Institución", "porcentaje": "Porcentaje (%)"},
                    color="seguridad_cat",
                    color_discrete_sequence=px.colors.qualitative.Set2
                )
                st.plotly_chart(fig, width='stretch')
            else:
                st.info(f"No hay datos de distribución para {anio_seleccionado}")
        else:
            st.info("Datos de distribución no disponibles")
    
    # ======================
    # Columna 2: Modelo de informalidad
    # ======================
    with col2:
        st.markdown("#### Factores que influyen en la informalidad")
        
        informalidad = cargar_csv(URLS.get("informalidad", ""))
        if informalidad is None:
            informalidad = cargar_desde_local("modelo_informalidad.csv")
        
        if informalidad is not None and not informalidad.empty:
            # Verificar columnas
            if "variable" in informalidad.columns and "coef" in informalidad.columns:
                # Filtrar solo variables principales (no estados) para el gráfico
                vars_principales = ["Intercept", "anios_esc", "exp", "exp2", "female"]
                df_plot = informalidad[informalidad["variable"].isin(vars_principales)]
                
                if not df_plot.empty:
                    fig = px.bar(
                        df_plot,
                        x="variable",
                        y="coef",
                        error_y="std_err" if "std_err" in informalidad.columns else None,
                        title="Factores que influyen en la informalidad",
                        labels={"coef": "Coeficiente", "variable": "Variable"}
                    )
                    st.plotly_chart(fig, width='stretch')
                else:
                    st.info("No hay coeficientes principales para graficar")
            else:
                st.warning("⚠️ El archivo de informalidad no tiene el formato esperado.")
                st.write("Columnas encontradas:", informalidad.columns.tolist())
            
            with st.expander("Ver tabla del modelo"):
                st.dataframe(informalidad)
        else:
            st.info("Datos de informalidad no disponibles")
    
    # ======================
    # Simulador de Probabilidad de Formalidad (CORREGIDO)
    # ======================
    st.subheader("📊 Simulador de Probabilidad de Formalidad")
    
    st.info("""
    Simula la probabilidad de tener empleo formal según tus características.
    **El modelo usa los coeficientes reales del Logit estimado con ENOE.**
    """)
    
    col1, col2 = st.columns(2)
    with col1:
        edad = st.slider("Edad", 18, 65, 30)
        educacion = st.slider("Años de educación", 0, 25, 12)
    with col2:
        sexo = st.selectbox("Sexo", ["Hombre", "Mujer"])
        estado = st.selectbox("Estado", [
            "Aguascalientes", "Baja California", "Baja California Sur", "Campeche",
            "Coahuila", "Colima", "Chiapas", "Chihuahua", "Ciudad de México",
            "Durango", "Guanajuato", "Guerrero", "Hidalgo", "Jalisco", "México",
            "Michoacán", "Morelos", "Nayarit", "Nuevo León", "Oaxaca", "Puebla",
            "Querétaro", "Quintana Roo", "San Luis Potosí", "Sinaloa", "Sonora",
            "Tabasco", "Tamaulipas", "Tlaxcala", "Veracruz", "Yucatán", "Zacatecas"
        ])
    
    # Mapeo de nombres de estado a códigos C(ent)[T.X] que usa el modelo
    estado_to_codigo = {
        "Aguascalientes": "C(ent)[T.1]",
        "Baja California": "C(ent)[T.2]",
        "Baja California Sur": "C(ent)[T.3]",
        "Campeche": "C(ent)[T.4]",
        "Coahuila": "C(ent)[T.5]",
        "Colima": "C(ent)[T.6]",
        "Chiapas": "C(ent)[T.7]",
        "Chihuahua": "C(ent)[T.8]",
        "Ciudad de México": "C(ent)[T.9]",
        "Durango": "C(ent)[T.10]",
        "Guanajuato": "C(ent)[T.11]",
        "Guerrero": "C(ent)[T.12]",
        "Hidalgo": "C(ent)[T.13]",
        "Jalisco": "C(ent)[T.14]",
        "México": "C(ent)[T.15]",
        "Michoacán": "C(ent)[T.16]",
        "Morelos": "C(ent)[T.17]",
        "Nayarit": "C(ent)[T.18]",
        "Nuevo León": "C(ent)[T.19]",
        "Oaxaca": "C(ent)[T.20]",
        "Puebla": "C(ent)[T.21]",
        "Querétaro": "C(ent)[T.22]",
        "Quintana Roo": "C(ent)[T.23]",
        "San Luis Potosí": "C(ent)[T.24]",
        "Sinaloa": "C(ent)[T.25]",
        "Sonora": "C(ent)[T.26]",
        "Tabasco": "C(ent)[T.27]",
        "Tamaulipas": "C(ent)[T.28]",
        "Tlaxcala": "C(ent)[T.29]",
        "Veracruz": "C(ent)[T.30]",
        "Yucatán": "C(ent)[T.31]",
        "Zacatecas": "C(ent)[T.32]"
    }
    
    # Intentar usar coeficientes reales del modelo
    prob = None
    if informalidad is not None and not informalidad.empty:
        try:
            # Crear diccionario de coeficientes
            coef_dict = dict(zip(informalidad["variable"], informalidad["coef"]))
            
            # Calcular experiencia
            exp = max(0, edad - educacion - 6)
            exp2 = exp ** 2
            
            # Coeficientes principales
            intercept = coef_dict.get("Intercept", 0)
            beta_educ = coef_dict.get("anios_esc", coef_dict.get("educacion", 0))
            beta_exp = coef_dict.get("exp", 0)
            beta_exp2 = coef_dict.get("exp2", 0)
            beta_female = coef_dict.get("female", 0)
            
            # Coeficiente del estado seleccionado
            estado_key = estado_to_codigo.get(estado, "")
            beta_estado = coef_dict.get(estado_key, 0)
            
            # Calcular logit
            z = (intercept + 
                 beta_educ * educacion + 
                 beta_exp * exp + 
                 beta_exp2 * exp2 + 
                 beta_female * (1 if sexo == "Mujer" else 0) + 
                 beta_estado)
            
            prob_informal = 1 / (1 + np.exp(-z))
            prob_formal = 1 - prob_informal
            prob = prob_formal
            st.caption(f"✅ Usando coeficientes del modelo Logit nacional (estado: {estado})")
        except Exception as e:
            st.warning(f"⚠️ Error al usar coeficientes del modelo: {e}. Usando fórmula simplificada.")
    
    # Fallback si no se pudo usar el modelo
    if prob is None:
        prob_base = 0.35
        prob_educ = educacion * 0.02
        prob_edad = 0.01 if 25 <= edad <= 50 else -0.02
        prob_sexo = -0.05 if sexo == "Mujer" else 0
        prob = prob_base + prob_educ + prob_edad + prob_sexo
        prob = max(0.05, min(0.85, prob))
        st.caption("⚙️ Usando fórmula simplificada (coeficientes del modelo no disponibles)")
    
    st.metric("Probabilidad estimada de formalidad", f"{prob:.1%}")
    
    # Mostrar coeficientes usados (debug)
    with st.expander("🔍 Ver coeficientes del modelo"):
        if informalidad is not None and not informalidad.empty:
            st.dataframe(informalidad)
        else:
            st.info("No hay coeficientes disponibles")

# ============================================
# TAB 5: ANÁLISIS SECTORIAL (COMPLETO Y CORREGIDO)
# ============================================
with tab5:
    st.subheader("🏭 Estructura y Retornos Sectoriales")
    
    # Función de carga específica para sectorial (detecta delimitador)
    @st.cache_data(ttl=3600)
    def cargar_sectorial():
        # Intentar desde URL
        try:
            response = requests.get(URLS.get("metricas_sectoriales", ""), timeout=60)
            if response.status_code == 200:
                content = response.content.decode('utf-8')
                # Detectar delimitador
                if content.count('|') > content.count(','):
                    df = pd.read_csv(BytesIO(response.content), delimiter='|', encoding='utf-8')
                else:
                    df = pd.read_csv(BytesIO(response.content), encoding='utf-8')
                if not df.empty:
                    return df
        except Exception as e:
            st.warning(f"No se pudo cargar desde URL: {e}")
        
        # Fallback local
        try:
            df = pd.read_csv("resultados/metricas_sectoriales.csv", encoding='utf-8')
            if not df.empty:
                return df
        except:
            pass
        
        try:
            df = pd.read_csv("resultados/metricas_sectoriales.csv", delimiter='|', encoding='utf-8')
            if not df.empty:
                return df
        except:
            pass
        
        return None
    
    # Cargar datos
    sectorial = cargar_sectorial()
    
    if sectorial is not None and not sectorial.empty:
        # Estandarizar nombres de columnas
        sectorial.columns = sectorial.columns.str.strip().str.lower()
        
        # 🔥 CONVERTIR formalidad a numérico (por si viene como string)
        if "formalidad" in sectorial.columns:
            sectorial["formalidad"] = pd.to_numeric(sectorial["formalidad"], errors="coerce")
            # Si la formalidad está en proporción (0-1), convertir a porcentaje
            if sectorial["formalidad"].max() <= 1:
                sectorial["formalidad_porcentaje"] = sectorial["formalidad"] * 100
            else:
                sectorial["formalidad_porcentaje"] = sectorial["formalidad"]
        
        # Verificar columnas necesarias
        required_cols = ["year", "sector", "ingreso_promedio", "formalidad", "beta_esc", "beta_formal"]
        missing = [col for col in required_cols if col not in sectorial.columns]
        
        if missing:
            st.warning(f"⚠️ Columnas faltantes: {missing}")
            st.info("Columnas disponibles: " + ", ".join(sectorial.columns.tolist()))
            # Si falta 'sector', intentar usar 'scian' y mapear
            if "sector" not in sectorial.columns and "scian" in sectorial.columns:
                scian_nombres = {
                    1: "Agropecuario", 2: "Minería", 3: "Energía", 4: "Construcción",
                    5: "Manufacturas", 6: "Comercio mayorista", 7: "Comercio minorista",
                    8: "Transporte", 9: "Medios", 10: "Finanzas", 11: "Inmobiliario",
                    12: "Prof./Cient./Téc.", 13: "Corporativos", 14: "Apoyo a negocios",
                    15: "Educación", 16: "Salud", 17: "Cultura/Deporte", 18: "Hospedaje/Alim.",
                    19: "Otros serv.", 20: "Gobierno"
                }
                sectorial["sector"] = sectorial["scian"].map(scian_nombres).fillna("Otros/No especificado")
            
            # Si falta 'formalidad', intentar usar 'formal'
            if "formalidad" not in sectorial.columns and "formal" in sectorial.columns:
                sectorial["formalidad"] = pd.to_numeric(sectorial["formal"], errors="coerce")
            elif "formalidad" not in sectorial.columns:
                sectorial["formalidad"] = sectorial["N"] / sectorial["N"].max()  # fallback
            
            # Reintentar verificar
            missing = [col for col in required_cols if col not in sectorial.columns]
            if missing:
                st.error(f"❌ Columnas necesarias aún faltantes: {missing}")
                st.dataframe(sectorial.head())
                st.stop()
        
        # 🔍 DIAGNÓSTICO: Mostrar estadísticas de formalidad
        with st.expander("🔍 Diagnóstico de formalidad"):
            st.write("Estadísticas de formalidad:")
            st.dataframe(sectorial[["year", "sector", "formalidad", "formalidad_porcentaje"]].head(10))
            st.write("Valores únicos de formalidad:", sectorial["formalidad"].unique()[:10])
        
        # Años disponibles
        years_available = sorted(sectorial["year"].unique())
        st.caption(f"📊 Años disponibles: {years_available}")
        
        # Selector de sector
        sectores = sorted(sectorial["sector"].unique())
        sector_seleccionado = st.selectbox("Selecciona un sector", ["Todos"] + sectores)
        
        # Filtrar
        if sector_seleccionado != "Todos":
            sectorial_filtrado = sectorial[sectorial["sector"] == sector_seleccionado]
        else:
            sectorial_filtrado = sectorial
        
        if sectorial_filtrado.empty:
            st.warning(f"No hay datos para {sector_seleccionado if sector_seleccionado != 'Todos' else 'ningún sector'}")
            st.stop()
        
        # Gráficos
        col1, col2 = st.columns(2)
        
        with col1:
            fig1 = px.line(
                sectorial_filtrado,
                x="year",
                y="ingreso_promedio",
                color="sector" if sector_seleccionado == "Todos" else None,
                title=f"Ingreso promedio por hora - {sector_seleccionado if sector_seleccionado != 'Todos' else 'Todos los sectores'}",
                labels={"ingreso_promedio": "Ingreso (pesos)", "year": "Año"}
            )
            st.plotly_chart(fig1, width='stretch')
        
        with col2:
            # 🔥 GRÁFICO DE FORMALIDAD CON PORCENTAJE
            if "formalidad_porcentaje" in sectorial_filtrado.columns:
                y_col = "formalidad_porcentaje"
                y_label = "Formalidad (%)"
            else:
                y_col = "formalidad"
                y_label = "Formalidad (proporción)"
            
            fig2 = px.line(
                sectorial_filtrado,
                x="year",
                y=y_col,
                color="sector" if sector_seleccionado == "Todos" else None,
                title=f"Tasa de formalidad - {sector_seleccionado if sector_seleccionado != 'Todos' else 'Todos los sectores'}",
                labels={y_col: y_label, "year": "Año"}
            )
            # Asegurar que el eje Y muestre porcentaje si corresponde
            if y_col == "formalidad_porcentaje":
                fig2.update_layout(yaxis=dict(tickformat=".1f", title="Formalidad (%)"))
            st.plotly_chart(fig2, width='stretch')
        
        # Betas por sector (último año)
        col3, col4 = st.columns(2)
        
        with col3:
            ultimo_anio = sectorial["year"].max()
            sectorial_ultimo = sectorial[sectorial["year"] == ultimo_anio].copy()
            
            # Filtrar betas válidas
            sectorial_ultimo_esc = sectorial_ultimo[sectorial_ultimo["beta_esc"].notna()]
            sectorial_ultimo_esc = sectorial_ultimo_esc.sort_values("beta_esc", ascending=False)
            
            if not sectorial_ultimo_esc.empty:
                fig3 = px.bar(
                    sectorial_ultimo_esc,
                    x="sector",
                    y="beta_esc",
                    title=f"Retorno a la escolaridad (β) por sector - {ultimo_anio}",
                    labels={"beta_esc": "β de Mincer", "sector": "Sector"},
                    color="beta_esc",
                    color_continuous_scale="Blues"
                )
                st.plotly_chart(fig3, width='stretch')
            else:
                st.info(f"No hay datos de beta_esc para {ultimo_anio}")
        
        with col4:
            sectorial_ultimo_formal = sectorial_ultimo[sectorial_ultimo["beta_formal"].notna()]
            sectorial_ultimo_formal = sectorial_ultimo_formal.sort_values("beta_formal", ascending=False)
            
            if not sectorial_ultimo_formal.empty:
                fig4 = px.bar(
                    sectorial_ultimo_formal,
                    x="sector",
                    y="beta_formal",
                    title=f"Prima de formalidad por sector - {ultimo_anio}",
                    labels={"beta_formal": "Coeficiente de formalidad", "sector": "Sector"},
                    color="beta_formal",
                    color_continuous_scale="Reds"
                )
                st.plotly_chart(fig4, width='stretch')
            else:
                st.info(f"No hay datos de beta_formal para {ultimo_anio}")
        
        # Tabla completa
        with st.expander("📋 Ver tabla completa de datos sectoriales"):
            st.dataframe(sectorial_filtrado.sort_values(["year", "sector"]))
        
        # Estadísticas resumen
        st.subheader("📊 Resumen sectorial")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Sectores con datos", sectorial["sector"].nunique())
        
        with col2:
            st.metric("Años disponibles", sectorial["year"].nunique())
        
        with col3:
            st.metric("Total de observaciones", f"{len(sectorial):,}")
    
    else:
        st.error("❌ No se pudieron cargar los datos sectoriales.")
        st.info("""
        **Para generar los datos sectoriales:**
        1. Ejecuta el script de reparación en `scripts/03_metricas.py`.
        2. Verifica que el archivo `resultados/metricas_sectoriales.csv` exista.
        3. Sube el archivo a Google Drive y actualiza el ID en `URLS`.
        """)

    
# ============================================
# FOOTER
# ============================================
st.markdown("---")
st.caption(
    "📊 **Monitor Laboral México** | Desarrollado por Santiago Alvarado | "
    "Basado en tesis de licenciatura UNAM | Datos: ENOE-INEGI"
)