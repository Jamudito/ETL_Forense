import pandas as pd
import numpy as np
from pathlib import Path

# =============================================================================
# 1. ARQUITECTURA DE RUTAS E INGESTA DEFENSIVA
# =============================================================================
print("[*] Iniciando ETL Forense - Normalización de Evidencia")

RUTA_ACTUAL = Path(__file__).parent
RUTA_EVIDENCIA = RUTA_ACTUAL / 'evidencia_dengue_cordoba.csv'

columnas_cargadas = [
    'tx_id', 'fecha_operacion', 'banco_origen', 'cuenta_origen', 
    'banco_destino', 'cuenta_destino', 'monto_transferido'
]

# Ingesta con separador '|'
df = pd.read_csv(RUTA_EVIDENCIA, sep='|', usecols=columnas_cargadas)

# =============================================================================
# 2. NORMALIZACIÓN TEMPORAL (Resolución tz-naive vs tz-aware)
# =============================================================================
numeros_crudos = pd.to_numeric(df['fecha_operacion'], errors='coerce')
mascara_num = numeros_crudos.notna()

# División de milisegundos a segundos para el motor de Unix
mascara_mili = mascara_num & (numeros_crudos > 9999999999)
numeros_crudos.loc[mascara_mili] = numeros_crudos.loc[mascara_mili] / 1000

fechas_num = pd.to_datetime(numeros_crudos[mascara_num], unit='s', utc=True)

# Aislamiento de cadenas de texto
mascara_text = ~mascara_num & df['fecha_operacion'].notna()
fechas_text = pd.to_datetime(
    df.loc[mascara_text, 'fecha_operacion'],
    format='mixed',
    dayfirst=True,
    errors='coerce',
    utc=True
)

# Ruteo a contenedor tz-aware (UTC estricto)
df['fechas_unificadas'] = pd.Series(pd.NaT, index=df.index, dtype='datetime64[ns, UTC]')
df.loc[mascara_num, 'fechas_unificadas'] = fechas_num
df.loc[mascara_text, 'fechas_unificadas'] = fechas_text

# =============================================================================
# 3. NORMALIZACIÓN DE ENTIDADES FINANCIERAS (Regex)
# =============================================================================
reglas_norm = {
    r"(?i).*mercado\s*pago.*|^mp$": "Mercado Pago",
    r"(?i).*galicia.*|.*bco\s*galicia.*": "Banco Galicia",
    r"(?i).*ual[áa].*": "Ualá",
    r"(?i).*naci[oó]n.*|.*bna.*": "Banco Nación"
}

df['banco_origen_norm'] = df['banco_origen'].astype(str).str.strip().replace(reglas_norm, regex=True)
df['banco_destino_norm'] = df['banco_destino'].astype(str).str.strip().replace(reglas_norm, regex=True)

# =============================================================================
# 4. CLASIFICACIÓN DE NODOS (CBU/CVU vs Alias)
# =============================================================================
df['cuenta_origen'] = df['cuenta_origen'].fillna("").astype(str).str.strip()
df['cuenta_destino'] = df['cuenta_destino'].fillna("").astype(str).str.strip()

# Vectorización pura en C backend para evaluación de longitud (22 dígitos)
df['tipo_origen'] = np.where(df['cuenta_origen'].str.match(r'^\d{22}$'), 'CBU/CVU',
                             np.where(df['cuenta_origen'] == "", 'Sin Datos', 'Alias'))
df['tipo_destino'] = np.where(df['cuenta_destino'].str.match(r'^\d{22}$'), 'CBU/CVU',
                              np.where(df['cuenta_destino'] == "", 'Sin Datos', 'Alias'))

# =============================================================================
# 5. EXTRACCIÓN FINANCIERA (Saneamiento de Divisas Mixtas)
# =============================================================================
# Remover caracteres no numéricos excepto punto y coma
montos_str = df['monto_transferido'].astype(str).str.replace(r'[^\d\.,]', '', regex=True)

# Detección de formato ARS (termina en coma y dos decimales)
mascara_arg = montos_str.str.contains(r',\d{1,2}$', na=False)

# Bifurcación lógica para homogeneizar a formato US (punto decimal)
montos_limpios = np.where(
    mascara_arg,
    montos_str.str.replace('.', '', regex=False).str.replace(',', '.', regex=False),
    montos_str.str.replace(',', '', regex=False)
)

montos_limpios = pd.Series(montos_limpios).replace('', np.nan)
df['montos_limpios'] = montos_limpios.astype(float)

# =============================================================================
# 6. AISLAMIENTO Y PROYECCIÓN FINAL
# =============================================================================
columnas_finales = [
    'tx_id', 'fechas_unificadas', 'banco_origen_norm', 'banco_destino_norm',
    'tipo_origen', 'tipo_destino', 'montos_limpios', 'cuenta_origen', 'cuenta_destino'
]
df_limpio = df[columnas_finales].copy()

print("\n[*] ETL Finalizado. Estructura de Memoria:")
print(df_limpio.info())
print("\n[*] Muestra de datos limpios:")
print(df_limpio.head())
