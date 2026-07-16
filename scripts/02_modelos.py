import os
import pandas as pd
import numpy as np
import statsmodels.api as sm
import statsmodels.formula.api as smf
import pymc as pm
import arviz as az
import warnings
warnings.filterwarnings("ignore")

os.makedirs("resultados", exist_ok=True)

def run_mincer_ols(df):
    """
    Ejecuta regresión Mincer OLS por año.
    """
    resultados = []
    for year, d in df.groupby("year"):
        d = d.dropna(subset=["lnw", "anios_esc", "exp", "exp2", "female", "formal"])
        if len(d) < 500:
            continue
        try:
            modelo = smf.ols("lnw ~ anios_esc + exp + exp2 + female + formal + C(scian)", data=d).fit(cov_type="HC1")
            resultados.append({
                "year": year,
                "N": len(d),
                "beta_esc": modelo.params.get("anios_esc", np.nan),
                "beta_exp": modelo.params.get("exp", np.nan),
                "beta_exp2": modelo.params.get("exp2", np.nan),
                "beta_female": modelo.params.get("female", np.nan),
                "beta_formal": modelo.params.get("formal", np.nan),
                "R2": modelo.rsquared,
                "AIC": modelo.aic,
                "BIC": modelo.bic
            })
        except Exception as e:
            print(f"⚠️ Error en OLS para {year}: {e}")
            continue
    return pd.DataFrame(resultados)

def run_quantile_mincer(df, quantiles=[0.1, 0.5, 0.9]):
    resultados = []
    for year, d in df.groupby("year"):
        d = d.dropna(subset=["lnw", "anios_esc", "exp", "exp2", "female"])
        if len(d) < 500:
            continue
        X = sm.add_constant(d[["anios_esc", "exp", "exp2", "female"]])
        y = d["lnw"]
        for q in quantiles:
            try:
                modelo = sm.QuantReg(y, X).fit(q=q)
                resultados.append({
                    "year": year,
                    "quantile": q,
                    "beta_esc": modelo.params.get("anios_esc", np.nan),
                    "beta_exp": modelo.params.get("exp", np.nan),
                    "beta_exp2": modelo.params.get("exp2", np.nan),
                    "beta_female": modelo.params.get("female", np.nan),
                })
            except Exception as e:
                print(f"⚠️ Error en QuantReg q={q} para {year}: {e}")
                continue
    return pd.DataFrame(resultados)

def run_bayesian_mincer(df, años=[2007, 2014, 2021, 2024]):
    """
    Modelo Bayesiano jerárquico con mejores priors.
    """
    resultados = []
    df = df[df["year"].isin(años)].copy()
    df = df.dropna(subset=["lnw", "anios_esc", "exp", "exp2", "female"])
    if df.empty:
        print("⚠️ No hay datos para el modelo Bayesiano.")
        return pd.DataFrame()

    # Estandarizar
    for col in ["anios_esc", "exp", "exp2"]:
        df[f"{col}_z"] = (df[col] - df[col].mean()) / df[col].std()
    
    df["year_id"] = df["year"].astype("category").cat.codes
    n_years = df["year_id"].nunique()

    n_sample = min(8000, len(df))
    idx = np.random.choice(len(df), n_sample, replace=False)
    
    esc_z = df["anios_esc_z"].values[idx]
    exp_z = df["exp_z"].values[idx]
    female = df["female"].values[idx]
    year_id = df["year_id"].values[idx]
    y = df["lnw"].values[idx]

    try:
        with pm.Model() as modelo_bayes:
            mu_alpha = pm.Normal("mu_alpha", 0, 1)
            sigma_alpha = pm.HalfNormal("sigma_alpha", 0.5)
            alpha_offset = pm.Normal("alpha_offset", 0, 1, shape=n_years)
            alpha = pm.Deterministic("alpha", mu_alpha + alpha_offset * sigma_alpha)
            
            beta_esc = pm.Normal("beta_esc", mu=0.08, sigma=0.05)
            beta_exp = pm.Normal("beta_exp", mu=0.04, sigma=0.02)
            beta_female = pm.Normal("beta_female", mu=-0.1, sigma=0.05)
            sigma = pm.HalfNormal("sigma", 0.5)

            mu = alpha[year_id] + beta_esc * esc_z + beta_exp * exp_z + beta_female * female
            pm.Normal("y_obs", mu=mu, sigma=sigma, observed=y)

            trace = pm.sample(
                draws=600,
                tune=800,
                chains=2,
                cores=1,
                target_accept=0.95,
                progressbar=True,
                random_seed=42
            )
        
        # Resumen
        summary = az.summary(trace, var_names=["beta_esc", "beta_exp", "beta_female"])
        
        # Extraer correctamente
        for param in summary.index:
            row = summary.loc[param]
            resultados.append({
                "param": param,
                "mean": row.get("mean", np.nan),
                "sd": row.get("sd", np.nan),
                "hdi_3%": row.get("hdi_3%", np.nan) if "hdi_3%" in row else row.get("hdi_3%", np.nan),
                "hdi_97%": row.get("hdi_97%", np.nan) if "hdi_97%" in row else row.get("hdi_97%", np.nan)
            })
        
        # 🔥 ELIMINADA la línea que guardaba el trace → ya no da error
        # az.to_netcdf(trace, "resultados/trace_bayesiano.nc")  # <--- COMENTADA
        
    except Exception as e:
        print(f"⚠️ Error en modelo Bayesiano: {e}")
    
    return pd.DataFrame(resultados)
def main():
    print("📊 Cargando datos limpios...")
    try:
        df = pd.read_csv("datos_brutos/datos_limpios.csv")
        print(f"✅ Datos cargados: {len(df):,} observaciones")
    except FileNotFoundError:
        print("❌ Archivo datos_brutos/datos_limpios.csv no encontrado.")
        print("Ejecuta primero 01_descarga_limpieza.py")
        return

    print("\n📈 Ejecutando Mincer OLS...")
    ols = run_mincer_ols(df)
    ols.to_csv("resultados/mincer_ols_por_anio.csv", index=False)
    print(f"✅ OLS: {len(ols)} años procesados")

    print("\n📈 Ejecutando Mincer Cuantílico...")
    quantile = run_quantile_mincer(df)
    quantile.to_csv("resultados/mincer_quantile_por_anio.csv", index=False)
    print(f"✅ Quantile: {len(quantile)} estimaciones")

    print("\n📈 Ejecutando Mincer Bayesiano...")
    bayes = run_bayesian_mincer(df)
    bayes.to_csv("resultados/bayes_por_anio.csv", index=False)
    print(f"✅ Bayesiano: {len(bayes)} parámetros estimados")

    print("\n✅ Todos los modelos ejecutados. Resultados en /resultados/")

if __name__ == "__main__":
    main()