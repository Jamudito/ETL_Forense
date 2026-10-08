# ETL_Forense
Pipeline de ingeniería de datos (Pandas/Regex) para estandarización de evidencia bancaria corrupta y detección de patrones PLA/AML.

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Pandas](https://img.shields.io/badge/Pandas-Vectorized-green.svg)
![Numpy](https://img.shields.io/badge/Numpy-Optimized-blueviolet.svg)

## 📌 Contexto del Problema
En el ecosistema de Prevención de Fraude y Lavado de Activos (PLA/AML), los equipos de investigación a menudo deben consolidar sábanas de datos provenientes de múltiples entidades financieras (Bancos Tradicionales, Fintechs, Exchanges de Criptomonedas). Estos reportes carecen de estandarización, presentando anomalías críticas:
- Delimitadores de ingesta inconsistentes.
- Formatos de tiempo mixtos (Timestamps Unix en segundos/milisegundos vs. Cadenas de texto) e incompatibilidad de zonas horarias (tz-naive vs tz-aware).
- Nomenclaturas de entidades fragmentadas.
- Regionalización mixta de divisas (separadores de miles y decimales en formato US y ARS coexistiendo en la misma columna).

Este proyecto es un **Pipeline ETL (Extract, Transform, Load) Forense** diseñado para ingestar evidencia bancaria corrupta y transformarla en una matriz de datos estructurada y unificada, lista para el perfilamiento financiero y el análisis de grafos, procesando grandes volúmenes de datos en milisegundos mediante **vectorización estricta**.

## 🛠️ Stack Tecnológico y Arquitectura Lógica
- **Pandas:** Ingesta defensiva optimizada (`usecols`, `dtype`) y ruteo de memoria RAM mediante máscaras booleanas.
- **NumPy (`np.where`):** Aplicación de lógica condicional anidada directamente en C para evitar iteraciones (`for loops`) costosas a nivel computacional, logrando escalabilidad.
- **Librería `re` (RegEx):** Compilación de expresiones regulares unificadas para el saneamiento rápido de *strings* (limpieza de divisas, estandarización de entidades, validación de CBU/CVU de 22 dígitos).
- **Pathlib:** Resolución dinámica de directorios para entornos de producción.

## ⚙️ Metodología Aplicada (Flujo del Script)
1. **Ingesta Defensiva:** Prevención de colapsos de memoria delimitando columnas estrictas y separadores dinámicos.
2. **Normalización Temporal Quirúrgica:** Uso de indexación booleana para bifurcar las marcas de tiempo. Los milisegundos se reducen a segundos mediante operaciones aritméticas vectorizadas, aislando los strings para el motor `to_datetime()`. Todo converge en una columna `datetime64[ns, UTC]` para prevenir colisiones de husos horarios.
3. **Estandarización de Entidades:** Implementación de diccionarios Regex (`(?i)`) para unificar variaciones de nomenclatura de bancos de origen y destino en un solo pase de compilación.
4. **Clasificación de Nodos:** Validación mediante Regex de la longitud estricta de 22 dígitos para clasificar cuentas entre `CBU/CVU` institucionales y `Alias` públicos.
5. **Saneamiento de Divisas Mixtas:** Detección inteligente de formato de moneda local mediante la identificación de patrones de cola (`r',\d{1,2}$'`). Conversión segura a formato de punto flotante para trazabilidad matemática de los fondos.

## 📊 Output
El pipeline devuelve un DataFrame inmutable (`df_limpio`) con calidad de producción. Los datos quedan listos para aplicar modelos de detección de anomalías, como la identificación de triangulación rápida (*cuentas mula*) o fugas de liquidez (*cash-out*).

*Nota: Los datasets utilizados para probar este script son mocks generados artificialmente para simular el ruido real de la industria. No contienen PII (Personal Identifiable Information) ni datos sensibles.*
