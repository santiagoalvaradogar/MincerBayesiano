import pandas as pd

# Cargar desde local
df_local = pd.read_csv("resultados/resumen_estado_anio.csv")
print("📋 Columnas:", df_local.columns.tolist())
print("\n📊 Valores únicos de formalidad:", df_local["formalidad"].unique()[:10])
print("\n📋 Primeras 10 filas:")
print(df_local[["ent", "year", "formalidad"]].head(10))

# Cargar desde Drive (si tienes el ID)
import requests
from io import BytesIO
url = "https://drive.google.com/uc?export=download&id=1EsbPoLoDo9fnlg1BU6CvM1a3pjJen4Fi"
response = requests.get(url)
df_drive = pd.read_csv(BytesIO(response.content))
print("\n📊 Desde Drive - valores únicos de formalidad:", df_drive["formalidad"].unique()[:10])