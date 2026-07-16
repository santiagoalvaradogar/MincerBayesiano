import pandas as pd
import numpy as np
import statsmodels.api as sm
import statsmodels.formula.api as smf
import os

os.makedirs("resultados", exist_ok=True)

# ============================================
# 1. CARGAR DATOS LIMPIOS
# ============================================
df = pd.read_csv("datos_brutos/datos_limpios.csv")
print(f"📊 Datos cargados: {len(df):,} observaciones")

# ============================================
# 2. MAPEO DE SCIAN A NOMBRES
# ============================================
scian_nombres = {
    1: "Agropecuario", 2: "Minería", 3: "Energía", 4: "Construcción",
    5: "Manufacturas", 6: "Comercio mayorista", 7: "Comercio minorista",
    8: "Transporte", 9: "Medios", 10: "Finanzas", 11: "Inmobiliario",
    12: "Prof./Cient./Téc.", 13: "Corporativos", 14: "Apoyo a negocios",
    15: "Educación", 16: "Salud", 17: "Cultura/Deporte", 18: "Hospedaje/Alim.",
    19: "Otros serv.", 20: "Gobierno"
}
df["sector"] = df["scian"].map(scian_nombres).fillna("Otros/No especificado")

# ============================================
# 3. CALCULAR MÉTRICAS SECTORIALES
# ============================================
resultados = []

for (year, sector), d in df.groupby(["year", "scian"]):
    # Tamaño de muestra mínimo
    if len(d) < 500:
        continue
    
    # Métricas básicas
    n = len(d)
    ingreso_promedio = d["salxhora"].mean()
    
    # **CORRECCIÓN: Asegurar que formalidad sea la proporción de formales**
    formalidad = d["formal"].mean() if "formal" in d.columns else 0
    
    # Estimar Mincer OLS por sector-año
    try:
        modelo = smf.ols("lnw ~ anios_esc + exp + exp2 + female + formal", data=d).fit(cov_type="HC1")
        beta_esc = modelo.params.get("anios_esc", np.nan)
        beta_formal = modelo.params.get("formal", np.nan)
        r2 = modelo.rsquared
    except Exception as e:
        print(f"⚠️ Error en año {year}, sector {sector}: {e}")
        beta_esc = np.nan
        beta_formal = np.nan
        r2 = np.nan
    
    resultados.append({
        "year": year,
        "scian": sector,
        "sector": scian_nombres.get(sector, "Otros/No especificado"),
        "N": n,
        "ingreso_promedio": ingreso_promedio,
        "formalidad": formalidad,
        "beta_esc": beta_esc,
        "beta_formal": beta_formal,
        "R2": r2
    })

# ============================================
# 4. GUARDAR
# ============================================
sectorial = pd.DataFrame(resultados)
sectorial.to_csv("resultados/metricas_sectoriales.csv", index=False)

print(f"\n✅ metricas_sectoriales.csv generado con {len(sectorial)} filas")
print(f"📋 Columnas: {list(sectorial.columns)}")
print(f"📅 Años disponibles: {sorted(sectorial['year'].unique())}")
print(f"🏭 Sectores: {sectorial['sector'].nunique()}")
print("\nPrimeras 5 filas:")
print(sectorial.head())