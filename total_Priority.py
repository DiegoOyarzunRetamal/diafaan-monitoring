import sys
import sqlite3
import datetime
import time
import importlib.util

# Rutas de configuración
db_config_path = r'C:/turuta\Monitor\OTP\Setting.ini'
license_config_path = r'C:\turuta\Monitor\OTP\License.py'  # Ruta modificada a License.py

# Configuración de reintentos y tiempo de espera
RETRIES = 3       # Número de reintentos en caso de bloqueo
TIMEOUT = 30      # Tiempo de espera en segundos para la conexión

# Verificar el número de argumentos
if len(sys.argv) != 2:
    print("Uso: python script.py <prioridad>")
    sys.exit(1)

# Obtener la prioridad del argumento
prioridad = sys.argv[1]

# Leer configuración de la base de datos desde Setting.ini
import configparser
db_config = configparser.ConfigParser()
db_config.read(db_config_path)

if 'BDSQLite' in db_config and 'db_path' in db_config['BDSQLite']:
    db_path = db_config.get('BDSQLite', 'db_path')
else:
    print("Error: La sección o clave de ruta de la base de datos no se encontró en Setting.ini")
    sys.exit(1)

# Cargar License.py desde la ruta especificada
spec = importlib.util.spec_from_file_location("license_config", license_config_path)
license_config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(license_config)

# Comprobar si la fecha de expiración es válida desde License.py
try:
    expiration_date_str = license_config.get_expiration_date()
    expiration_date = datetime.datetime.strptime(expiration_date_str, '%Y-%m-%d').date()

    if datetime.date.today().date() > expiration_date:
        print("CRITICAL: El script ha caducado.")
        sys.exit(2)
except AttributeError:
    print("ERROR: No se encontró la fecha de expiración en License.py")
    sys.exit(1)

# Consultar la base de datos
query = """
SELECT Priority, 
       COUNT(*) AS total_registros
FROM SendQueue
WHERE Priority = ?
GROUP BY Priority;
"""

# Función para ejecutar consulta con reintentos
def execute_query_with_retries(db_path, query, params):
    attempt = 0
    while attempt < RETRIES:
        try:
            conn = sqlite3.connect(db_path, timeout=TIMEOUT)
            cursor = conn.cursor()
            cursor.execute(query, params)
            resultados = cursor.fetchall()
            conn.close()
            return resultados
        except sqlite3.OperationalError as e:
            if 'database is locked' in str(e):
                print(f"Advertencia: La base de datos está bloqueada. Intento {attempt + 1}/{RETRIES}")
                attempt += 1
                time.sleep(2)  # Esperar antes del siguiente intento
            else:
                raise e
    raise sqlite3.OperationalError("No se pudo ejecutar la consulta debido al bloqueo de la base de datos.")

# Ejecutar la consulta con reintentos
try:
    resultados = execute_query_with_retries(db_path, query, (prioridad,))
    if resultados:
        for fila in resultados:
            prioridad_actual = fila[0]
            total_registros = fila[1]
            
            # Salida para Nagios
            if total_registros > 0:
                print(f'CRITICAL: Hay {total_registros} mensajes con prioridad {prioridad_actual}')
                print(f'| total_registros={total_registros};0;100;0;')
                sys.exit(2)
            else:
                print(f'OK: No hay mensajes con prioridad {prioridad_actual}')
                print(f'| total_registros={total_registros};0;100;0;')
                sys.exit(0)
    else:
        print(f'OK: No hay mensajes con prioridad {prioridad}')
        print(f'| total_registros=0;0;100;0;')
        sys.exit(0)
except sqlite3.OperationalError as e:
    print(f"Error: {e}")
    sys.exit(1)
