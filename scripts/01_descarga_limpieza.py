import os
import pandas as pd
import numpy as np
import requests
import zipfile
from io import BytesIO
import time
import glob

# ==============================
# FUNCIONES DE DESCARGA
# ==============================

def descargar_enoé(año, trimestre):
    """
    Descarga la ENOE usando la estructura correcta de URLs del INEGI.
    """
    if año <= 2020 and trimestre <= 2:
        url = f"https://www.inegi.org.mx/contenidos/programas/enoe/15ymas/microdatos/{año}trim{trimestre}_csv.zip"
    else:
        url = f"https://www.inegi.org.mx/contenidos/programas/enoe/15ymas/microdatos/enoe_{año}_trim{trimestre}_csv.zip"
    
    print(f"    Intentando: {url}")
    
    try:
        response = requests.get(url, timeout=60)
        if response.status_code != 200:
            print(f"    ⚠️ Código HTTP {response.status_code}")
            return None
        
        if len(response.content) < 1000:
            print(f"    ⚠️ Archivo muy pequeño (posible error)")
            return None
            
        if not response.content[:4] == b'PK\x03\x04':
            print(f"    ⚠️ No es un archivo ZIP válido")
            return None
        
        with zipfile.ZipFile(BytesIO(response.content)) as z:
            archivos = [f for f in z.namelist() if "sdem" in f.lower()]
            if not archivos:
                archivos = [f for f in z.namelist() if f.endswith('.csv')]
            if not archivos:
                print(f"    ⚠️ No se encontró archivo CSV en el ZIP")
                return None
            
            archivo_elegido = archivos[0]
            print(f"    📄 Leyendo: {archivo_elegido}")
            
            with z.open(archivo_elegido) as f:
                for encoding in ["utf-8", "latin1", "ISO-8859-1"]:
                    try:
                        df = pd.read_csv(f, encoding=encoding, low_memory=False)
                        print(f"    ✅ Decodificado con {encoding}")
                        return df
                    except UnicodeDecodeError:
                        f.seek(0)
                        continue
                return None
                
    except Exception as e:
        print(f"    ❌ Error: {e}")
        return None

# ==============================
# LIMPIEZA CORREGIDA (sin duplicados)
# ==============================

def limpiar_enoé(df, año):
    """
    Limpia la ENOE con manejo robusto de columnas.
    """
    if df is None or df.empty:
        print("⚠️ DataFrame vacío o nulo.")
        return None
    
    # Normalizar nombres
    df.columns = df.columns.str.strip().str.lower()
    
    # Diagnóstico
    print(f"    📋 Columnas encontradas en el archivo de {año}:")
    print(f"       {list(df.columns)}")
    print(f"    📋 Primeras 2 filas (para referencia):")
    print(df.head(2).to_string())
    print("-" * 50)

    # Mapeo de nombres: cada columna se asigna a un solo nombre canónico
    # Usamos un diccionario que mapea nombres originales a canónicos
    rename_map = {}
    # Definimos correspondencias
    correspondencias = {
        'eda': ['eda', 'edad'],
        'ent': ['ent', 'estado', 'entidad'],
        'sex': ['sex', 'sexo'],
        'anios_esc': ['anios_esc', 'escolaridad', 'educacion'],
        'hrsocup': ['hrsocup', 'horas'],
        'ingocup': ['ingocup', 'ingreso'],
        'imssissste': ['imssissste', 'seguridad', 'imss'],
        'scian': ['scian', 'actividad'],
        'emp_ppal': ['emp_ppal'],
        'n_hij': ['n_hij', 'hijos'],
        'e_con': ['e_con', 'estado_civil']
    }
    
    # Para cada columna existente, buscar si coincide con algún canónico
    for col in df.columns:
        for canonico, alternativas in correspondencias.items():
            if col in alternativas:
                rename_map[col] = canonico
                break  # Una columna solo se renombra una vez
    
    # Aplicar renombres
    if rename_map:
        print(f"    🔄 Renombrando columnas: {rename_map}")
        df = df.rename(columns=rename_map)
    
    # Verificar columnas necesarias
    needed = ['eda', 'ent', 'sex', 'anios_esc', 'hrsocup', 'ingocup', 'imssissste', 'scian']
    missing = [col for col in needed if col not in df.columns]
    if missing:
        print(f"    ❌ Columnas necesarias faltantes: {missing}")
        print(f"    💡 Columnas disponibles: {list(df.columns)}")
        return None
    
    # Convertir a numérico (solo columnas que existen)
    for col in needed:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Filtrar
    df = df[df['eda'] >= 18]
    df = df[df['eda'] <= 65]
    df = df[df['hrsocup'] >= 6]
    df = df[df['hrsocup'] <= 98]
    df = df[df['ingocup'] > 0]
    
    # Eliminar valores 99
    for col in needed:
        if col in df.columns:
            df = df[df[col] != 99]
    
    # Sexo válido
    df = df[df['sex'].isin([1, 2])]
    
    # Calcular variables
    df['salxhora'] = df['ingocup'] / df['hrsocup']
    df['lnw'] = np.log(df['salxhora'] + 0.01)
    df['exp'] = (df['eda'] - df['anios_esc'] - 6).clip(lower=0)
    df['exp2'] = df['exp'] ** 2
    df['formal'] = (df['imssissste'] > 0).astype(int)
    df['female'] = (df['sex'] == 2).astype(int)
    df['year'] = año
    
    # Columnas finales
    final_cols = ['year', 'ent', 'sex', 'eda', 'anios_esc', 'exp', 'exp2', 
                  'lnw', 'salxhora', 'ingocup', 'hrsocup', 'formal', 'female', 
                  'scian', 'imssissste', 'n_hij', 'e_con']
    final_cols = [col for col in final_cols if col in df.columns]
    df = df[final_cols].dropna()
    
    print(f"    ✅ Limpieza exitosa: {len(df):,} observaciones")
    return df

# ==============================
# DATOS SIMULADOS (FALLBACK)
# ==============================

def generar_datos_simulados():
    np.random.seed(42)
    años = [2007, 2010, 2013, 2016, 2019, 2022, 2024]
    probs_educ = np.array([
        0.05, 0.10, 0.15, 0.15, 0.12, 0.10, 0.08, 0.06, 0.05, 0.04,
        0.03, 0.02, 0.02, 0.01, 0.01, 0.005, 0.005, 0.005, 0.005, 0.005,
        0.005, 0.005, 0.005, 0.005, 0.005
    ])
    probs_educ = probs_educ / probs_educ.sum()
    
    dfs = []
    for año in años:
        n = np.random.randint(8000, 15000)
        df = pd.DataFrame({
            "year": año,
            "ent": np.random.randint(1, 33, n),
            "sex": np.random.choice([1, 2], n, p=[0.48, 0.52]),
            "eda": np.random.randint(18, 65, n),
            "anios_esc": np.random.choice(range(0, 25), n, p=probs_educ),
            "hrsocup": np.random.randint(20, 60, n),
            "n_hij": np.random.choice(range(0, 6), n, p=[0.3, 0.25, 0.2, 0.15, 0.07, 0.03]),
            "e_con": np.random.choice([1, 2, 3, 4], n, p=[0.4, 0.3, 0.2, 0.1])
        })
        exp = (df["eda"] - df["anios_esc"] - 6).clip(min=0)
        df["exp"] = exp
        df["exp2"] = exp ** 2
        beta0 = 1.5 + (año - 2007) * 0.02
        beta_esc = 0.08 - (año - 2007) * 0.002
        beta_exp = 0.04 - (año - 2007) * 0.001
        beta_exp2 = -0.0006 + (año - 2007) * 0.00002
        beta_fem = -0.1 + (año - 2007) * 0.002
        lnw = (beta0 + beta_esc * df["anios_esc"] + 
               beta_exp * df["exp"] + beta_exp2 * df["exp2"] + 
               beta_fem * (df["sex"] == 2) + np.random.normal(0, 0.35, n))
        df["salxhora"] = np.exp(lnw)
        df["lnw"] = lnw
        df["ingocup"] = df["salxhora"] * df["hrsocup"]
        formal_prob = 0.3 + (año - 2007) * 0.01 + 0.1 * (df["anios_esc"] / 25) - 0.1 * (df["sex"] == 2)
        df["formal"] = (np.random.random(n) < formal_prob.clip(0.1, 0.8)).astype(int)
        df["female"] = (df["sex"] == 2).astype(int)
        df["scian"] = np.random.choice(range(1, 22), n)
        df["imssissste"] = df["formal"] * np.random.choice([1, 2, 3], n, p=[0.6, 0.25, 0.15]) + (1 - df["formal"]) * 4
        dfs.append(df)
    return pd.concat(dfs, ignore_index=True)

# ==============================
# FUNCIÓN PRINCIPAL
# ==============================

def main():
    os.makedirs("datos_brutos", exist_ok=True)
    
    # Intentar archivos locales
    archivos_locales = glob.glob("datos_brutos/*.csv")
    if archivos_locales:
        print(f"📁 Encontrados {len(archivos_locales)} archivos locales en datos_brutos/")
        dfs = []
        for f in archivos_locales:
            try:
                df = pd.read_csv(f)
                dfs.append(df)
                print(f"  ✅ Cargado: {f}")
            except Exception as e:
                print(f"  ⚠️ Error al cargar {f}: {e}")
        if dfs:
            df_total = pd.concat(dfs, ignore_index=True)
            df_total.to_csv("datos_brutos/datos_limpios.csv", index=False)
            print(f"✅ Datos combinados guardados: {len(df_total):,} observaciones")
            return
    
    # Descargar
    print("📥 Intentando descarga desde INEGI (trimestre 1 de cada año)...")
    años = list(range(2007, 2025))
    dfs = []
    
    for año in años:
        print(f"\n  Procesando año {año}...")
        df = descargar_enoé(año, 1)
        if df is not None:
            df_limpio = limpiar_enoé(df, año)
            if df_limpio is not None and not df_limpio.empty:
                dfs.append(df_limpio)
                print(f"  ✅ {año}: {len(df_limpio):,} observaciones")
                continue
        print(f"  ⚠️ {año}: no se pudo descargar o limpiar")
        time.sleep(1)
    
    if not dfs:
        print("\n⚠️ No se pudo descargar ningún año. Generando datos simulados...")
        df_sim = generar_datos_simulados()
        df_sim.to_csv("datos_brutos/datos_limpios.csv", index=False)
        print(f"✅ Datos simulados guardados: {len(df_sim):,} observaciones")
    else:
        df_total = pd.concat(dfs, ignore_index=True)
        df_total.to_csv("datos_brutos/datos_limpios.csv", index=False)
        print(f"\n✅ Datos guardados: {len(df_total):,} observaciones totales")
    
    print("📊 Archivo guardado en: datos_brutos/datos_limpios.csv")

if __name__ == "__main__":
    main()