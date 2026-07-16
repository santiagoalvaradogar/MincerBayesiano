import os
import pandas as pd
import numpy as np
import statsmodels.api as sm
import statsmodels.formula.api as smf

print("📊 Recalculando formalidad con definición correcta...")

# Cargar datos limpios
df = pd.read_csv("datos_brutos/datos_limpios.csv")
print(f"✅ Datos cargados: {len(df):,} observaciones")

# Recalcular formalidad: IMSS (1), ISSSTE (2), Otras instituciones (3) = FORMAL
# No recibe atención médica (4) = INFORMAL
# No especificado (5 o NaN) = excluir
df["formal_correcta"] = np.nan
df.loc[df["imssissste"].isin([1, 2, 3]), "formal_correcta"] = 1
df.loc[df["imssissste"] == 4, "formal_correcta"] = 0
# Eliminar casos donde no se sabe (5, NaN)
df = df[df["formal_correcta"].notna()].copy()
print(f"✅ Después de excluir 'No especificado': {len(df):,} observaciones")

# Verificar distribución
print("\n📊 Distribución de formalidad (nueva):")
print(df["formal_correcta"].value_counts())
print(f"Tasa de formalidad: {df['formal_correcta'].mean():.2%}")

# Mapeo de códigos SCIAN a nombres
scian_nombres = {
    1: "Agropecuario", 2: "Minería", 3: "Energía", 4: "Construcción",
    5: "Manufacturas", 6: "Comercio mayorista", 7: "Comercio minorista",
    8: "Transporte", 9: "Medios", 10: "Finanzas", 11: "Inmobiliario",
    12: "Prof./Cient./Téc.", 13: "Corporativos", 14: "Apoyo a negocios",
    15: "Educación", 16: "Salud", 17: "Cultura/Deporte", 18: "Hospedaje/Alim.",
    19: "Otros serv.", 20: "Gobierno"
}
df["sector"] = df["scian"].map(scian_nombres).fillna("Otros/No especificado")

# Recalcular métricas sectoriales con formalidad corregida
resultados = []

for (year, sector), d in df.groupby(["year", "scian"]):
    if len(d) < 500:
        continue
    
    n = len(d)
    ingreso_prom = d["salxhora"].mean()
    formalidad = d["formal_correcta"].mean()
    
    # Estimar Mincer OLS
    try:
        modelo = smf.ols("lnw ~ anios_esc + exp + exp2 + female + formal_correcta", data=d).fit(cov_type="HC1")
        beta_esc = modelo.params.get("anios_esc", np.nan)
        beta_formal = modelo.params.get("formal_correcta", np.nan)
        r2 = modelo.rsquared
    except:
        beta_esc = np.nan
        beta_formal = np.nan
        r2 = np.nan
    
    resultados.append({
        "year": year,
        "scian": sector,
        "sector": scian_nombres.get(sector, "Otros/No especificado"),
        "N": n,
        "ingreso_promedio": ingreso_prom,
        "formalidad": formalidad,
        "beta_esc": beta_esc,
        "beta_formal": beta_formal,
        "R2": r2
    })

# Guardar nuevo archivo
df_sectorial = pd.DataFrame(resultados)
output_path = "resultados/metricas_sectoriales_formalidad_corregida.csv"
df_sectorial.to_csv(output_path, index=False)

print(f"\n✅ Nuevo archivo guardado: {output_path}")
print(f"📋 Filas: {len(df_sectorial)}")
print(f"📅 Años: {sorted(df_sectorial['year'].unique())}")
print("\n📊 Muestra de formalidad por sector (primeros años):")
print(df_sectorial[["year", "sector", "formalidad", "N"]].head(10))