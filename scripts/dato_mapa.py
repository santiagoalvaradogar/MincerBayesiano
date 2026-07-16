import pandas as pd
import statsmodels.formula.api as smf
import numpy as np

# Cargar datos limpios
df = pd.read_csv("datos_brutos/datos_limpios.csv")
print(f"✅ Datos cargados: {len(df):,} observaciones")

# Calcular beta de Mincer por estado y año
resultados = []

for (year, ent), d in df.groupby(["year", "ent"]):
    if len(d) < 500:
        continue
    
    try:
        modelo = smf.ols("lnw ~ anios_esc + exp + exp2 + female + formal", data=d).fit(cov_type="HC1")
        beta_esc = modelo.params.get("anios_esc", np.nan)
        resultados.append({
            "year": year,
            "ent": ent,
            "beta_esc": beta_esc,
            "N": len(d)
        })
    except:
        continue

# Guardar
df_beta = pd.DataFrame(resultados)
df_beta.to_csv("resultados/beta_mincer_estado_anio.csv", index=False)
print(f"✅ beta_mincer_estado_anio.csv generado con {len(df_beta)} filas")
print(f"Años disponibles: {sorted(df_beta['year'].unique())}")