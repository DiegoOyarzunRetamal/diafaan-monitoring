# -*- coding: utf-8 -*-
"""
Script: Q_completo.py
Autor: Diego Oyarzun Retamal
Fecha de creación: 2024-09-25
Versión: 1.0
Descripción:
    Consulta en la base de datos SQLite la cantidad de mensajes en la tabla `sendqueue` 
    para un conjunto de `gatewayid` activos definidos manualmente.
    Retorna todos los resultados en una sola línea para integración con Nagios 
    o herramientas de monitoreo.

Uso:
    python Q_completo.py

Ejemplo de salida:
    2=10  3=0  5=4  6=0  7=2 ...

Dependencias:
    - Python 3.x
    - sqlite3 (incluido en la librería estándar)
    - configparser (incluido en la librería estándar)

Archivos requeridos:
    - Setting.ini   → contiene la ruta del archivo SQLite (sección [BDSQLite])
    - License.py    → contiene función get_expiration_date()
"""

import sys
import sqlite3
import time
import importlib.util
from datetime import datetime
import configparser

# Archivos de configuración (ajustar según entorno)
db_config_path = r'C:\turuta\Monitor\OTP\Setting.ini'
license_config_path = r'C:\turuta\Monitor\OTP\License.py'

# Configuración de reintentos y timeout
TIMEOUT = 60   # segundos de espera en conexión SQLite
RETRIES = 3    # número de reintentos en caso de error

# Leer configuración de la base de datos desde Setting.ini
db_config = configparser.ConfigParser()
db_config.read(db_config_path)

if 'BDSQLite' in db_config and 'db_path' in db_config['BDSQLite']:
    db_path = db_config.get('BDSQLite', 'db_path')
else:
    print("Error: No se encontró la sección [BDSQLite] o la clave db_path en Setting.ini")
    sys.exit(1)

# Cargar License.py y validar expiración
spec = importlib.util.spec_from_file_location("license_config", license_config_path)
license_config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(license_config)

try:
    expiration_date_str = license_config.get_expiration_date()
    expiration_date = datetime.strptime(expiration_date_str, '%Y-%m-%d').date()
    if datetime.today().date() > expiration_date:
        print("CRITICAL: El script ha caducado.")
        sys.exit(2)
except AttributeError:
    print("ERROR: No se encontró la fecha de expiración en License.py")
    sys.exit(1)

# Lista de gatewayid activos a monitorear (ajustar según entorno)
active_gateways = [2, 3, 5, 6, 7, 8, 9, 15, 16, 19]

def execute_query_with_retries(db_path, query, params=(), retries=RETRIES):
    """
    Ejecuta una consulta SQLite con reintentos en caso de fallo.
    """
    attempt = 0
    while attempt < retries:
        try:
            conn = sqlite3.connect(db_path, timeout=TIMEOUT)
            cursor = conn.cursor()
            cursor.execute(query, params)
            resultados = cursor.fetchall()
            conn.close()
            return resultados
        except sqlite3.OperationalError:
            attempt += 1
            time.sleep(2)  # espera antes de reintentar
    raise sqlite3.OperationalError("No se pudo ejecutar la consulta después de varios intentos.")

# Consulta SQL para contar mensajes por gatewayid activo
count_query = f"""
SELECT gatewayid,
       COUNT(*) AS total_registros
FROM sendqueue
WHERE gatewayid IN ({','.join('?' for _ in active_gateways)})
GROUP BY gatewayid;
"""

try:
    resultados = execute_query_with_retries(db_path, count_query, params=active_gateways)

    # Convertir resultados en diccionario
    counts = {int(gatewayid): count for gatewayid, count in resultados}

    # Generar salida (ejemplo: "2=10  3=0  5=4")
    messages = [f"{gatewayid}={counts.get(gatewayid, 0)}" for gatewayid in active_gateways]
    print("  ".join(messages))

except sqlite3.OperationalError as e:
    print(f"Error: {e}")
    sys.exit(1)
