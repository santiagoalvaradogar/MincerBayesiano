import pandas as pd

# Cargar tus datos limpios (local)
df = pd.read_csv("datos_brutos/datos_limpios.csv")

# Calcular métricas por estado y año
resumen = df.groupby(["ent", "year"]).agg(
    salario_promedio=("salxhora", "mean"),
    lnw_promedio=("lnw", "mean"),
    educacion_promedio=("anios_esc", "mean"),
    formalidad=("formal", "mean"),
    N=("salxhora", "count")
).reset_index()

# Guardar el resumen (¡pesa muy poco!)
resumen.to_csv("resumen_estado_anio.csv", index=False)
print("✅ Resumen guardado en resumen_estado_anio.csv")