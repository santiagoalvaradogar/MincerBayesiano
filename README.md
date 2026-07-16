# Monitor del Mercado Laboral Mexicano 📊

Este proyecto es un sistema completo y automatizado para el monitoreo, modelado y análisis del mercado laboral mexicano utilizando los microdatos de la **Encuesta Nacional de Ocupación y Empleo (ENOE)** del INEGI.

El sistema calcula indicadores clave de desigualdad, estima retornos a la educación a través de ecuaciones de Mincer (frecuentista, cuantílica y bayesiana jerárquica) y realiza análisis sectoriales dinámicos en un **Dashboard interactivo en Streamlit**.

---

## 🚀 Características del Proyecto

1. **Pipeline de Datos Automatizado**: Descarga directa de la ENOE desde el servidor de INEGI, limpieza de datos con filtros de edad (18-65 años), horas de trabajo a la semana (20-98 horas), recorte de valores atípicos y cálculo de la experiencia potencial.
2. **Modelos Econométricos**:
   - **Regresión OLS Mincer**: $\ln(w) = \beta_0 + \beta_1 S + \beta_2 E + \beta_3 E^2 + \beta_4 Female + \beta_5 Formal + \mu$.
   - **Regresión Cuantílica**: Evaluación de retornos a la educación en diferentes cuantiles de ingreso (Q10, Q50, Q90).
   - **Modelo Bayesiano Jerárquico**: Modelado multinivel con `PyMC` y `ArviZ` para analizar la variación temporal y estatal del retorno educativo.
3. **Métricas de Desigualdad y Género**:
   - Índices de Gini y Theil de ingresos por hora.
   - Descomposición salarial de **Oaxaca-Blinder** para calcular la brecha de género explicada vs. no explicada (discriminación).
   - Modelo logístico (Logit) para estimar la probabilidad de informalidad.
4. **Análisis Sectorial (SCIAN)**: Estadísticas desagregadas por sector económico (agropecuario, manufactura, servicios, etc.) que muestran la evolución del ingreso promedio, tasa de formalidad y la prima de formalidad por sector.
5. **Automatización en la Nube**: GitHub Actions ejecuta de manera trimestral el pipeline y sube los resultados calculados a Terabox.

---

## 📁 Estructura del Repositorio

```
MincerBayesiano/
├── .github/
│   └── workflows/
│       └── update_data.yml     # Workflow de GitHub Actions (ejecución trimestral)
├── dashboard/
│   └── app.py                  # Aplicación del Dashboard de Streamlit
├── datos_brutos/
│   └── .gitkeep                # Carpeta para microdatos ENOE descargados (ignorados por Git)
├── resultados/
│   └── .gitkeep                # CSVs e hiperparámetros generados (ignorados por Git)
├── scripts/
│   ├── 01_descarga_limpieza.py # Descarga microdatos y genera simulación si está offline
│   ├── 02_modelos.py           # Estimación de modelos OLS, cuantílicos y bayesianos (PyMC)
│   ├── 03_metricas.py          # Cálculo de Gini, Theil, Oaxaca-Blinder, Logit y SCIAN
│   └── 04_subir_terabox.py     # Script para subir resultados calculados a Terabox
├── .gitignore                  # Reglas de archivos excluidos del control de versiones
├── requirements.txt            # Dependencias del entorno de Python
└── README.md                   # Descripción y guía del proyecto
```

---

## 🔧 Instalación y Requisitos

Se recomienda utilizar un entorno virtual de Python 3.10 o superior:

```bash
# 1. Clonar el repositorio
git clone https://github.com/TU_USUARIO/MincerBayesiano.git
cd MincerBayesiano

# 2. Crear y activar el entorno virtual
python -m venv .venv
# En Windows:
.venv\Scripts\activate
# En macOS/Linux:
source .venv/bin/activate

# 3. Instalar las dependencias
pip install -r requirements.txt
```

---

## 📊 Ejecución Local

Para ejecutar todo el pipeline de análisis y desplegar el dashboard localmente, sigue esta secuencia:

```bash
# Paso 1: Descargar y limpiar datos (ENOE/Simulación)
python scripts/01_descarga_limpieza.py

# Paso 2: Ejecutar los modelos econométricos (OLS, Cuantílico y Bayesiano)
python scripts/02_modelos.py

# Paso 3: Calcular métricas de desigualdad, género y sectores
python scripts/03_metricas.py

# Paso 4: Lanzar el Dashboard interactivo
streamlit run dashboard/app.py
```

---

## 🌐 Despliegue en Streamlit Cloud

1. Sube tu código a un repositorio público en GitHub.
2. Ve a [share.streamlit.io](https://share.streamlit.io/) e inicia sesión con tu cuenta de GitHub.
3. Haz clic en **New app** y selecciona el repositorio `MincerBayesiano`, la rama `main` y la ruta del archivo `dashboard/app.py`.
4. Haz clic en **Deploy!** y tu dashboard estará en línea.

*Enlace al dashboard en vivo:* [https://share.streamlit.io/TU_USUARIO/mincerbayesiano/main/dashboard/app.py](https://share.streamlit.io/)

---

## 🔐 Configuración de Secretos (GitHub Secrets)

Para habilitar la actualización automática trimestral mediante GitHub Actions y subir los datos generados a tu cuenta de Terabox, debes configurar las siguientes variables en **Settings > Secrets and variables > Actions** de tu repositorio:

- `TERABOX_JSTOKEN`
- `TERABOX_CSRF`
- `TERABOX_BROWSERID`
- `TERABOX_NDUS`
- `TERABOX_NDUT_FMT`
- `TERABOX_LANG` (Opcional, por defecto `en`)

---

## 📝 Licencia

Este proyecto está bajo la Licencia MIT.
