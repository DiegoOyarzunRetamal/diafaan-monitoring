# -*- coding: utf-8 -*-
"""
Script: GW_errors.py
Autor: Diego Oyarzun Retamal
Fecha de creación: 2024-09-25
Versión: 1.0
Descripción:
    Verifica la cantidad de errores en un gateway específico 
    a partir del campo StatusCode en la base de datos SQLite 
    de Diafaan Message Server.
    Retorna códigos estándar de Nagios y métricas para PNP4Nagios.

Uso:
    python GW_errors.py <GatewayId> <ErrorCode> [--error_threshold N] [--critical_threshold N]

Ejemplo:
    python GW_errors.py 2 300 --error_threshold 5000 --critical_threshold 10000

Dependencias:
    - Python 3.x
    - sqlite3 (incluido en la librería estándar)

Archivos requeridos:
    - MessageLog.sqlite (ubicación configurada en db_path)

Nota de seguridad:
    ⚠️ Ajustar la ruta de la base de datos (`db_path`) según entorno.
"""

import sqlite3
import sys
import argparse

# Ruta de la base de datos SQLite (ajustar según entorno)
db_path = r'C:\ProgramData\Diafaan\Diafaan Message Server\MessageLog.sqlite'

# Argumentos CLI
parser = argparse.ArgumentParser(description="Script para verificar errores en un gateway específico.")
parser.add_argument("gateway_id", help="ID del gateway a verificar.")
parser.add_argument("error_code", help="Código de error a verificar (e.g., 300).")
parser.add_argument("--error_threshold", type=int, default=5000, help="Umbral de advertencia (default: 5000).")
parser.add_argument("--critical_threshold", type=int, default=10000, help="Umbral crítico (default: 10000).")
args = parser.parse_args()

gateway_id = args.gateway_id
error_code = args.error_code
error_threshold = args.error_threshold
critical_threshold = args.critical_threshold


def execute_query(db_path, query, params):
    """
    Ejecuta una consulta SQLite y devuelve resultados.
    Retorna lista de filas o lanza excepción si ocurre error.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(query, params)
        resultados = cursor.fetchall()
        conn.close()
        return resultados
    except sqlite3.Error as e:
        print(f"UNKNOWN: Error de base de datos: {e}")
        sys.exit(3)


# Consulta SQL para contar errores
query = """
SELECT COUNT(*) AS TotalError
FROM MessageOut
WHERE StatusCode = ?
AND GatewayId = ?;
"""

try:
    resultados = execute_query(db_path, query, (error_code, gateway_id))
    total_error = resultados[0][0] if resultados else 0

    # Datos de rendimiento para Nagios/PNP4Nagios
    performance_data = f"total_error={total_error};{error_threshold};{critical_threshold};0;"

    # Evaluar estado según thresholds
    if total_error > critical_threshold:
        print(f"CRITICAL: {total_error} errors with code {error_code} in gateway {gateway_id} | {performance_data}")
        sys.exit(2)
    elif total_error > error_threshold:
        print(f"WARNING: {total_error} errors with code {error_code} in gateway {gateway_id} | {performance_data}")
        sys.exit(1)
    else:
        print(f"OK: {total_error} errors with code {error_code} in gateway {gateway_id} | {performance_data}")
        sys.exit(0)

except Exception as e:
    print(f"UNKNOWN: Failed to execute check. Error: {str(e)}")
    sys.exit(3)
