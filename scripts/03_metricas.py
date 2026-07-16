import os
import pandas as pd
import numpy as np
import statsmodels.api as sm
import statsmodels.formula.api as smf

os.makedirs("resultados", exist_ok=True)

# =============================================
# FUNCIÓN: GINI
# =============================================
def calcular_gini(x):
    x = np.array(x, dtype=float)
    x = x[np.isfinite(x) & (x > 0)]
    if len(x) == 0:
        return np.nan
    x = np.sort(x)
    n = len(x)
    cumsum = np.cumsum(x)
    gini = (2 * np.sum((np.arange(1, n+1) * x)) / (n * np.sum(x))) - (n + 1) / n
    return gini

# =============================================
# FUNCIÓN: THEIL
# =============================================
def calcular_theil(x):
    x = np.array(x, dtype=float)
    x = x[np.isfinite(x) & (x > 0)]
    if len(x) == 0:
        return np.nan
    mu = x.mean()
    r = x / mu
    return np.mean(r * np.log(r))

# =============================================
# FUNCIÓN: OAXACA-BLINDER
# =============================================
def oaxaca_blinder(df, año):
    d = df[df["year"] == año].dropna(subset=["lnw", "anios_esc", "exp", "exp2", "female", "formal"])
    if d.empty or len(d) < 500:
        return None
    hombres = d[d["female"] == 0]
    mujeres = d[d["female"] == 1]
    if len(hombres) < 200 or len(mujeres) < 200:
        return None
    vars_ = ["anios_esc", "exp", "exp2", "formal"]
    X_h = sm.add_constant(hombres[vars_])
    X_m = sm.add_constant(mujeres[vars_])
    y_h = hombres["lnw"]
    y_m = mujeres["lnw"]
    mod_h = sm.OLS(y_h, X_h).fit()
    mod_m = sm.OLS(y_m, X_m).fit()
    X_pool = sm.add_constant(d[vars_])
    mod_pool = sm.OLS(d["lnw"], X_pool).fit()
    X_h_mean = X_h.mean()
    X_m_mean = X_m.mean()
    gap = y_h.mean() - y_m.mean()
    explained = (X_h_mean - X_m_mean) @ mod_pool.params
    unexplained = gap - explained
    return {
        "year": año,
        "gap": gap,
        "explained": explained,
        "unexplained": unexplained,
        "N_hombres": len(hombres),
        "N_mujeres": len(mujeres)
    }

# =============================================
# FUNCIÓN: MODELO DE INFORMALIDAD (LOGIT)
# =============================================
def modelo_informalidad(df):
    """
    Estima un modelo Logit para la probabilidad de ser informal.
    Informal = 1 si imssissste == 4 (No recibe atención médica).
    """
    # Definir variable dependiente
    df["informal"] = (df["imssissste"] == 4).astype(int)
    
    # Seleccionar variables
    vars_modelo = ["anios_esc", "exp", "exp2", "female", "ent"]
    d = df.dropna(subset=["informal"] + vars_modelo).copy()
    
    if d.empty:
        print("⚠️ No hay datos para el modelo de informalidad")
        return pd.DataFrame()
    
    # Verificar que haya variación en la variable dependiente
    if d["informal"].nunique() < 2:
        print("⚠️ No hay variación en la variable dependiente (informal). Todos son iguales.")
        return pd.DataFrame()
    
    try:
        # Modelo Logit
        modelo = smf.logit("informal ~ anios_esc + exp + exp2 + female + C(ent)", data=d).fit(disp=False)
        
        # Extraer tabla de coeficientes
        tabla = modelo.summary().tables[1]
        
        # Convertir a DataFrame
        coefs = []
        for row in tabla.data[1:]:  # Saltar encabezado
            if len(row) >= 7:
                coefs.append({
                    "variable": row[0],
                    "coef": float(row[1]),
                    "std_err": float(row[2]),
                    "z": float(row[3]),
                    "p_value": float(row[4]),
                    "lower_ci": float(row[5]),
                    "upper_ci": float(row[6])
                })
        
        out = pd.DataFrame(coefs)
        print(f"✅ Modelo de informalidad: {len(out)} coeficientes estimados")
        return out
        
    except Exception as e:
        print(f"⚠️ Error en modelo de informalidad: {e}")
        return pd.DataFrame()

# =============================================
# FUNCIÓN: DISTRIBUCIÓN DE SEGURIDAD SOCIAL
# =============================================
def distribucion_seguridad(df):
    """
    Calcula la distribución porcentual de las categorías de IMSS/ISSSTE por año.
    """
    def clasificar_seguridad(x):
        if x == 1:
            return "IMSS"
        elif x == 2:
            return "ISSSTE"
        elif x == 3:
            return "Otras instituciones"
        elif x == 4:
            return "No recibe atención médica"
        else:
            return "No especificado"
    
    df["seguridad_cat"] = df["imssissste"].apply(clasificar_seguridad)
    
    distribucion = df.groupby(["year", "seguridad_cat"]).size().reset_index(name="count")
    distribucion["porcentaje"] = distribucion.groupby("year")["count"].transform(lambda x: 100 * x / x.sum())
    
    return distribucion

# =============================================
# FUNCIÓN: MÉTRICAS SECTORIALES (SCIAN)
# =============================================
def metricas_sectoriales(df):
    """
    Calcula métricas por sector (scian) y año:
    - Número de trabajadores.
    - Ingreso promedio por hora.
    - Tasa de formalidad.
    - Retorno a la escolaridad (β de Mincer OLS).
    - Prima de formalidad (coeficiente de formalidad en OLS).
    """
    resultados = []
    
    for (year, sector), d in df.groupby(["year", "scian"]):
        if len(d) < 500:
            continue
        
        # Métricas básicas
        n = len(d)
        ingreso_prom = d["salxhora"].mean()
        formalidad = d["formal"].mean()
        
        # Modelo Mincer para retorno educativo
        try:
            modelo = smf.ols("lnw ~ anios_esc + exp + exp2 + female + formal", data=d).fit(cov_type="HC1")
            beta_esc = modelo.params.get("anios_esc", np.nan)
            beta_formal = modelo.params.get("formal", np.nan)
        except:
            beta_esc = np.nan
            beta_formal = np.nan
        
        resultados.append({
            "year": year,
            "scian": sector,
            "N": n,
            "ingreso_promedio": ingreso_prom,
            "formalidad": formalidad,
            "beta_esc": beta_esc,
            "beta_formal": beta_formal
        })
    
    return pd.DataFrame(resultados)

# =============================================
# MAIN
# =============================================
def main():
    print("📊 Cargando datos limpios...")
    try:
        df = pd.read_csv("datos_brutos/datos_limpios.csv")
        print(f"✅ Datos cargados: {len(df):,} observaciones")
    except FileNotFoundError:
        print("❌ Archivo datos_brutos/datos_limpios.csv no encontrado.")
        print("Ejecuta primero 01_descarga_limpieza.py")
        return

    # 1. Gini y Theil
    print("\n📈 Calculando Gini y Theil...")
    metricas = []
    for year, d in df.groupby("year"):
        salario = d["salxhora"].values
        metricas.append({
            "year": year,
            "gini": calcular_gini(salario),
            "theil": calcular_theil(salario),
            "N": len(d)
        })
    pd.DataFrame(metricas).to_csv("resultados/gini_theil_por_anio.csv", index=False)
    print("✅ Gini y Theil guardados")

    # 2. Oaxaca-Blinder
    print("\n📈 Calculando Oaxaca-Blinder...")
    oaxaca = []
    for year in sorted(df["year"].unique()):
        res = oaxaca_blinder(df, year)
        if res:
            oaxaca.append(res)
    if oaxaca:
        pd.DataFrame(oaxaca).to_csv("resultados/oaxaca_blinder_por_anio.csv", index=False)
        print("✅ Oaxaca-Blinder guardado")

    # 3. Modelo de informalidad (CORREGIDO)
    print("\n📈 Modelo de informalidad...")
    logit = modelo_informalidad(df)
    if not logit.empty:
        logit.to_csv("resultados/modelo_informalidad.csv", index=False)
        print("✅ Modelo de informalidad guardado")
    else:
        print("⚠️ No se pudo generar el modelo de informalidad")

    # 4. Distribución de seguridad social
    print("\n📈 Distribución de seguridad social...")
    dist = distribucion_seguridad(df)
    if not dist.empty:
        dist.to_csv("resultados/distribucion_seguridad.csv", index=False)
        print("✅ Distribución de seguridad guardada")

    # 5. Métricas sectoriales
    print("\n📈 Métricas sectoriales (SCIAN)...")
    sectorial = metricas_sectoriales(df)
    if not sectorial.empty:
        sectorial.to_csv("resultados/metricas_sectoriales.csv", index=False)
        print("✅ Métricas sectoriales guardadas")

    print("\n✅ Todas las métricas calculadas. Resultados en /resultados/")

if __name__ == "__main__":
    main()