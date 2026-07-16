import pandas as pd
import numpy as np
import statsmodels.api as sm
import statsmodels.formula.api as smf

# Cargar datos limpios
df = pd.read_csv("datos_brutos/datos_limpios.csv")
print(f"✅ Datos cargados: {len(df):,} observaciones")

# Función Oaxaca-Blinder por estado (corregida)
def oaxaca_twofold_estado(d):
    """
    Calcula Oaxaca-Blinder twofold para un DataFrame de un estado.
    Retorna gap, explained, unexplained.
    Usa 'sex' (1=hombre, 2=mujer) y crea 'male' internamente.
    """
    X_VARS = ["anios_esc", "exp", "exp2", "hrsocup"]
    CAT_VARS = ["scian"]

    # Crear variable male (1=hombre, 0=mujer)
    d = d.copy()
    d["male"] = (d["sex"] == 1).astype(int)

    def _design(xx):
        X = xx[X_VARS].copy()
        for c in X.columns:
            X[c] = pd.to_numeric(X[c], errors="coerce")
        for cat in CAT_VARS:
            ser = pd.to_numeric(xx[cat], errors="coerce").fillna(-1).astype("int64").astype("category")
            dum = pd.get_dummies(ser, prefix=cat, drop_first=True)
            X = pd.concat([X, dum], axis=1)
        X = sm.add_constant(X, has_constant="add")
        return X

    d = d.dropna(subset=["lnw"] + X_VARS).copy()
    if d.empty or d["male"].nunique() < 2:
        return None

    Xp = _design(d)
    mask = np.isfinite(Xp.to_numpy(dtype=float)).all(axis=1) & np.isfinite(d["lnw"].to_numpy(dtype=float))
    d, Xp = d.loc[mask].copy(), Xp.loc[mask].copy()

    f = d[d["male"] == 0]  # mujeres
    m = d[d["male"] == 1]  # hombres
    if len(f) < 100 or len(m) < 100:
        return None

    cols = Xp.columns
    Xf = _design(f).reindex(columns=cols, fill_value=0)
    Xm = _design(m).reindex(columns=cols, fill_value=0)

    y = d["lnw"].to_numpy(float)
    yf = f["lnw"].to_numpy(float)
    ym = m["lnw"].to_numpy(float)
    Xp_np = Xp.to_numpy(float)
    Xfbar = Xf.to_numpy(float).mean(axis=0)
    Xmbar = Xm.to_numpy(float).mean(axis=0)

    bp = sm.OLS(y, Xp_np).fit().params
    gap = float(ym.mean() - yf.mean())
    explained = float((Xmbar - Xfbar) @ bp)
    unexplained = float(gap - explained)
    return {"gap": gap, "explained": explained, "unexplained": unexplained}

# Calcular por estado y año
resultados = []

for (year, ent), d in df.groupby(["year", "ent"]):
    if len(d) < 500:
        continue
    try:
        res = oaxaca_twofold_estado(d)
        if res:
            resultados.append({
                "year": int(year),
                "ent": int(ent),
                "gap": res["gap"],
                "explained": res["explained"],
                "unexplained": res["unexplained"]
            })
    except Exception as e:
        print(f"Error en {year}-{ent}: {e}")
        continue

# Guardar
df_oaxaca = pd.DataFrame(resultados)
if not df_oaxaca.empty:
    df_oaxaca.to_csv("resultados/oaxaca_estado_anio.csv", index=False)
    print(f"✅ oaxaca_estado_anio.csv generado con {len(df_oaxaca)} filas")
    print(f"Años disponibles: {sorted(df_oaxaca['year'].unique())}")
else:
    print("❌ No se generaron resultados. Revisa los datos.")