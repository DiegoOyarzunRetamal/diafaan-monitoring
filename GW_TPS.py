# -*- coding: utf-8 -*-
"""
Script: GW_TPS.py
Autor: Diego Oyarzun Retamal
Fecha de creación: 2024-09-25
Versión: 1.0
Descripción:
    Calcula las transacciones por segundo (TPS) de un Gateway específico 
    en Diafaan utilizando una consulta a SQL Server.
    Retorna códigos compatibles con Nagios y métricas para PNP4Nagios.

Uso:
    python GW_TPS.py <GatewayName>

Ejemplo:
    python GW_TPS.py SMPP_Gateway_1

Dependencias:
    - Python 3.x
    - pyodbc

Archivos requeridos:
    - Setting.ini   → contiene parámetros de conexión SQL (sección [sqlodbc])
    - License.py    → contiene función get_expiration_date()


"""

import pyodbc
import argparse
import sys
import configparser
import importlib.util
from datetime import datetime

# Archivos de configuración (ajustar según entorno)
db_config_path = r'C:\turuta\Monitor\OTP\Setting.ini'
license_config_path = r'C:\turuta\Monitor\OTP\License.py'

# Leer configuración de base de datos desde Setting.ini
db_config = configparser.ConfigParser()
db_config.read(db_config_path)

# Cargar License.py desde la ruta especificada
spec = importlib.util.spec_from_file_location("license_config", license_config_path)
license_config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(license_config)

# Validar fecha de expiración de licencia
try:
    expiration_date_str = license_config.get_expiration_date()
    expiration_date = datetime.strptime(expiration_date_str, '%Y-%m-%d').date()

    if datetime.today().date() > expiration_date:
        print("CRITICAL: El script ha caducado.")
        sys.exit(2)
except AttributeError:
    print("ERROR: No se encontró la fecha de expiración en License.py")
    sys.exit(1)

# Argumentos de entrada
parser = argparse.ArgumentParser(
    description="Script para calcular las transacciones por segundo (TPS) de un gateway específico."
)
parser.add_argument("gateway_name", help="Nombre del gateway a verificar.")
args = parser.parse_args()

gateway_name = args.gateway_name
warning_threshold = 4
critical_threshold = 1

# Validar parámetros de conexión
if 'sqlodbc' in db_config:
    conn_str = (
        f"DRIVER={db_config.get('sqlodbc', 'driver')};"
        f"SERVER={db_config.get('sqlodbc', 'server')};"
        f"DATABASE={db_config.get('sqlodbc', 'database')};"
        f"UID={db_config.get('sqlodbc', 'uid')};"
        f"PWD={db_config.get('sqlodbc', 'pwd')};"
    )
else:
    print("ERROR: No se encontró la sección 'sqlodbc' en el archivo de configuración.")
    sys.exit(1)

# Ejecutar consulta a SQL Server
try:
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    sql_query = f"""
        SELECT 
            CAST (COUNT(*) AS decimal(18,10)) / 60.0 AS TPS
        FROM dbo.messagelog
        WHERE SendTime >= DATEADD(second, -60, GETDATE())
        AND Gateway = '{gateway_name}';
    """

    cursor.execute(sql_query)
    result = cursor.fetchone()

    if result:
        tps = result[0]
        performance_data = f"tps={tps:.2f};{warning_threshold};{critical_threshold};0;"

        if tps < critical_threshold:
            print(f"CRITICAL: {tps:.2f} TPS en gateway {gateway_name} | {performance_data}")
            sys.exit(2)
        elif tps < warning_threshold:
            print(f"WARNING: {tps:.2f} TPS en gateway {gateway_name} | {performance_data}")
            sys.exit(1)
        else:
            print(f"OK: {tps:.2f} TPS en gateway {gateway_name} | {performance_data}")
            sys.exit(0)
    else:
        print(f"UNKNOWN: No se encontraron transacciones para el gateway '{gateway_name}' en el intervalo de tiempo especificado.")
        sys.exit(3)

except pyodbc.Error as e:
    print(f"UNKNOWN: Error al conectarse a la base de datos o ejecutar la consulta: {e}")
    sys.exit(3)

finally:
    if 'conn' in locals() and conn is not None:
        conn.close()
