import pandas as pd
import numpy as np
from pathlib import Path

RUTA_ACTUAL = Path(__file__).parent
ruta_evidencia = RUTA_ACTUAL / 'evidencia_dengue_cordoba.csv'

columnas_cargadas = [
    'tx_id', 'fecha_operacion', 'banco_origen', 'cuenta_origen', 
    'banco_destino', 'cuenta_destino', 'monto_transferido'
]

df = pd.read_csv(ruta_evidencia, sep='|', usecols=columnas_cargadas )
# NORMALIZACION FECHAS
numeros_crudos = pd.to_numeric(df['fecha_operacion'], errors='coerce')

mascara_num = numeros_crudos.notna()

mascara_mili = mascara_num & (numeros_crudos > 9999999999)
numeros_crudos.loc[mascara_mili] = numeros_crudos.loc[mascara_mili] / 1000

fechas_num = pd.to_datetime(numeros_crudos[mascara_num], unit='s', utc=True)

mascara_text = ~mascara_num & df['fecha_operacion'].notna()

fechas_text = pd.to_datetime(
    df.loc[mascara_text, 'fecha_operacion'],
    format='mixed',
    dayfirst=True,
    errors='coerce',
    utc=True
)

df['fechas_unificadas'] = pd.Series(pd.NaT, index=df.index, dtype='datetime64[ns, UTC]')

df.loc[mascara_num, 'fechas_unificadas'] = fechas_num
df.loc[mascara_text, 'fechas_unificadas'] = fechas_text

# NORMALIZACION ENTIDADES FINANCIERAS
reglas_norm = {
    r"(?i).*mercado\s*pago.*|^mp$": "Mercado Pago",
    r"(?i).*galicia.*|.*bco\s*galicia.*": "Banco Galicia",
    r"(?i).*ual[áa].*": "Ualá",
    r"(?i).*naci[oó]n.*|.*bna.*": "Banco Nación"
}

df['banco_origen_norm'] = df['banco_origen'].astype(str).str.strip().replace(reglas_norm, regex=True)
df['banco_destino_norm'] = df['banco_destino'].astype(str).str.strip().replace(reglas_norm, regex=True)

# NORMALIZACION CBU/CVU
df['cuenta_origen'] = df['cuenta_origen'].fillna("").astype(str).str.strip()
df['cuenta_destino'] = df['cuenta_destino'].fillna("").astype(str).str.strip()

df['tipo_origen'] = np.where(df['cuenta_origen'].str.match(r'^\d{22}$'), 'CBU/CVU',
                             np.where(df['cuenta_origen'] == "", 'Sin Datos', 'Alias'))
df['tipo_destino'] = np.where(df['cuenta_destino'].str.match(r'^\d{22}$'), 'CBU/CVU',
                              np.where(df['cuenta_destino'] == "", 'Sin Datos', 'Alias'))

# NORMALIZACION DIVISAS MIXTAS
montos_str = df['monto_transferido'].astype(str).str.replace(r'[^\d\.,]', '', regex=True)

mascara_arg = montos_str.str.contains(r',\d{1,2}$', na=False)

montos_limpios = np.where(
    mascara_arg,
    montos_str.str.replace('.', '', regex=False).str.replace(',', '.', regex=False),
    montos_str.str.replace(',', '', regex=False)
)

montos_limpios = pd.Series(montos_limpios).replace('', np.nan)
df['montos_limpios'] = montos_limpios.astype(float)

columnas_finales = [
    'tx_id', 'fechas_unificadas', 'banco_origen_norm', 'banco_destino_norm',
    'tipo_origen', 'tipo_destino', 'montos_limpios', 'cuenta_origen', 'cuenta_destino'
]
df_limpio = df[columnas_finales].copy()

print("\n[*] ETL Finalizado. Estructura de Memoria:")
print(df_limpio.info())
print("\n[*] Muestra de datos limpios:")
print(df_limpio.head())