# -*- coding: utf-8 -*-
"""
Script: MessagesInSendQueue.py
Autor: Diego Oyarzun Retamal
Fecha de creación: 2024-09-25
Versión: 1.0
Descripción:
    Consulta el valor de `MessagesInSendQueue` desde la API XML de Diafaan.
    Integra con Nagios, retornando:
        - 0 = OK si se obtiene el valor correctamente.
        - 2 = CRITICAL en caso de error de conexión o parsing.

Uso:
    python MessagesInSendQueue.py

Ejemplo de salida:
    OK - MessagesInSendQueue: 45 | messages_in_send_queue=45

Dependencias:
    - Python 3.x
    - requests

Archivos requeridos:
    - Setting.ini   → contiene la URL de la API (sección [URL], clave api_url)
    - License.py    → contiene función get_expiration_date()

Nota de seguridad:
    ⚠️ No exponer Setting.ini ni License.py en repositorios públicos.
"""

import requests
import xml.etree.ElementTree as ET
import sys
import configparser
import datetime
import importlib.util

# Archivos de configuración (ajustar según entorno)
url_config_path = r'C:\turuta\Monitor\OTP\Setting.ini'
license_config_path = r'C:\turuta\Monitor\OTP\License.py'

# Leer configuración de la URL desde Setting.ini
url_config = configparser.ConfigParser()
url_config.read(url_config_path)

if 'URL' in url_config and 'api_url' in url_config['URL']:
    url = url_config.get('URL', 'api_url')
else:
    print("Error: La sección [URL] o la clave api_url no se encontró en Setting.ini")
    sys.exit(1)

# Validar licencia desde License.py
spec = importlib.util.spec_from_file_location("license_config", license_config_path)
license_config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(license_config)

try:
    expiration_date_str = license_config.get_expiration_date()
    expiration_date = datetime.datetime.strptime(expiration_date_str, '%Y-%m-%d').date()
    if datetime.date.today() > expiration_date:
        print("CRITICAL: El script ha caducado.")
        sys.exit(2)
except AttributeError:
    print("ERROR: No se encontró la fecha de expiración en License.py")
    sys.exit(1)

# Consultar API XML
try:
    response = requests.get(url, timeout=10)
    response.raise_for_status()
except requests.exceptions.RequestException as e:
    print(f"CRITICAL - Error al conectar con la API: {e}")
    sys.exit(2)

# Parsear XML y extraer valor
try:
    root = ET.fromstring(response.content)
    statistics = root.find('.//Statistics')
    messages_in_send_queue = statistics.find('MessagesInSendQueue').text
    print(f"OK - MessagesInSendQueue: {messages_in_send_queue} | messages_in_send_queue={messages_in_send_queue}")
    sys.exit(0)
except Exception as e:
    print(f"CRITICAL - Error al obtener MessagesInSendQueue: {e}")
    sys.exit(2)
